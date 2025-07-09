import json
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  TemplateView, UpdateView)

from .models import (Card, CardKnowledge, CardSharing, GameLog, GameSession,
                     Player, PlayerCard, initialize_cluedo_cards)

logger = logging.getLogger(__name__)


class BaseGameView(TemplateView):
    """Vista base con contesto comune per tutte le viste del gioco."""
    
    def get_local_ip(self):
        """Ottieni l'indirizzo IP locale."""
        return GameSession.get_local_ip()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['local_ip'] = self.get_local_ip()
        context['debug'] = True  # Imposta a False in produzione
        return context


class HomeView(BaseGameView):
    """Homepage principale con opzioni per creare o unirsi a una sessione."""
    template_name = 'index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Cluedo Tracker - Gestione Carte in Rete Locale',
            'active_sessions_count': GameSession.objects.filter(is_active=True).count(),
        })
        return context


class HostHomeView(BaseGameView):
    """Homepage per l'host per creare e gestire sessioni."""
    template_name = 'host_home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_sessions = GameSession.objects.filter(is_active=True).prefetch_related('players')
        
        context.update({
            'title': 'Host Dashboard - Cluedo Tracker',
            'active_sessions': active_sessions,
            'total_players': sum(session.player_count for session in active_sessions),
        })
        return context


class CreateSessionView(CreateView):
    """Crea una nuova sessione di gioco."""
    model = GameSession
    fields = ['name', 'max_players', 'allow_card_sharing', 'auto_reveal_cards']
    template_name = 'create_session.html'
    
    def form_valid(self, form):
        # Inizializza le carte se non esistono
        if not Card.objects.exists():
            initialize_cluedo_cards()
            logger.info("Carte Cluedo inizializzate nel database")
        
        response = super().form_valid(form)
        
        # Log creazione sessione
        GameLog.objects.create(
            session=self.object,
            action_type='session_created',
            description=f'Sessione "{self.object.name}" creata',
            data={
                'session_code': self.object.session_code,
                'max_players': self.object.max_players,
                'host_ip': self.object.host_ip,
            }
        )
        
        messages.success(
            self.request, 
            f'Sessione creata! Codice: {self.object.session_code}'
        )
        return response
    
    def get_success_url(self):
        return reverse('host_session', kwargs={'session_code': self.object.session_code})


class HostSessionView(BaseGameView):
    """Vista host per gestire una sessione specifica."""
    template_name = 'host_session.html'
    
    def get(self, request, *args, **kwargs):
        session_code = self.kwargs['session_code']
        try:
            session = GameSession.objects.get(session_code=session_code)
            if not session.is_active:
                messages.error(request, 'Questa sessione è stata terminata o non è più attiva.')
                return redirect('host_home')
        except GameSession.DoesNotExist:
            messages.error(request, 'Sessione non trovata.')
            return redirect('host_home')
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_code = self.kwargs['session_code']
        session = get_object_or_404(GameSession, session_code=session_code)
        
        players = session.players.filter(is_active=True).prefetch_related('cards')
        cards = Card.objects.all().order_by('card_type', 'name')
        
        context.update({
            'session': session,
            'session_code': session_code,
            'title': f'Host - {session.name}',
            'players': players,
            'cards': cards,
            'websocket_url': f'ws://{context["local_ip"]}:8000/ws/session/{session_code}/',
            'mobile_url': f'http://{context["local_ip"]}:8000/join/{session_code}/',
            'qr_url': reverse('session_qr', kwargs={'session_code': session_code}),
            'recent_activity': session.logs.all()[:10],
        })
        return context


class JoinSessionView(BaseGameView):
    """Pagina per unirsi a una sessione esistente."""
    template_name = 'session_join.html'
    
    def get(self, request, *args, **kwargs):
        session_code = self.kwargs.get('session_code', '')
        if session_code:
            try:
                # Controlla che la sessione esista ed sia attiva
                GameSession.objects.get(session_code=session_code, is_active=True)
            except GameSession.DoesNotExist:
                messages.error(request, 'Questa sessione non esiste o è stata terminata.')
                return redirect('home')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_code = self.kwargs.get('session_code', '')
        if session_code:
            try:
                session = GameSession.objects.get(session_code=session_code, is_active=True)
                context['session'] = session
                context['auto_fill_code'] = session_code
                context['users_count'] = session.player_count
                context['max_users'] = session.max_players
                # Ottieni personaggi già presi
                taken_characters = list(session.players.filter(is_active=True).values_list('character', flat=True))
                context['taken_characters'] = taken_characters
            except GameSession.DoesNotExist:
                # Non aggiungere nulla, il redirect è già gestito nel get
                pass
        context.update({
            'title': 'Unisciti alla Sessione',
            'character_choices': Player.CHARACTERS,
            'session_code': session_code,
            'weapons': Card.objects.filter(card_type='weapon').order_by('name'),
            'rooms': Card.objects.filter(card_type='room').order_by('name'),
        })
        return context
    
    def post(self, request, *args, **kwargs):
        session_code = request.POST.get('session_code', '').upper().strip()
        player_name = request.POST.get('player_name', '').strip()
        character = request.POST.get('character', '')
        device_id = request.POST.get('device_id', '')
        
        # Gestione carte iniziali
        initial_cards_json = request.POST.get('initial_cards', '[]')
        try:
            initial_cards = json.loads(initial_cards_json) if initial_cards_json else []
        except json.JSONDecodeError:
            initial_cards = []
        
        # Validazione input
        if not all([session_code, player_name, character]):
            messages.error(request, 'Tutti i campi sono obbligatori.')
            return self.get(request, *args, **kwargs)
        
        try:
            session = GameSession.objects.get(session_code=session_code, is_active=True)
        except GameSession.DoesNotExist:
            messages.error(request, f'Sessione con codice "{session_code}" non trovata.')
            return self.get(request, *args, **kwargs)
        
        # Controlla se il personaggio è già preso
        if session.players.filter(character=character, is_active=True).exists():
            messages.error(request, 'Personaggio già selezionato da un altro giocatore.')
            return self.get(request, *args, **kwargs)
        
        # Controlla numero massimo di giocatori
        if session.player_count >= session.max_players:
            messages.error(request, 'Sessione piena.')
            return self.get(request, *args, **kwargs)
        
        # Crea o aggiorna giocatore
        try:
            with transaction.atomic():
                # Prima controlla se questo giocatore esiste già nella sessione
                existing_player = session.players.filter(name=player_name, is_active=True).first()
                
                if existing_player:
                    # Il giocatore esiste già, aggiorna il personaggio
                    existing_player.character = character
                    existing_player.save()
                    player = existing_player
                    created = False
                else:
                    # Crea nuovo giocatore
                    player = Player.objects.create(
                        session=session,
                        name=player_name,
                        character=character,
                        is_active=True
                    )
                    created = True
                
                # Gestisci le carte iniziali se fornite
                if initial_cards:
                    self._process_initial_cards(player, initial_cards)
                
                # Salva informazioni del giocatore nella sessione
                request.session['player_name'] = player_name
                request.session['session_code'] = session_code
                request.session['player_id'] = player.id
                if device_id:
                    request.session['device_id'] = device_id
                
                # Log ingresso giocatore
                GameLog.objects.create(
                    session=session,
                    player=player,
                    action_type='player_joined',
                    description=f'{player_name} si è unito come {player.get_character_display()}',
                    data={'character': character, 'created': created, 'initial_cards_count': len(initial_cards)}
                )
                
                messages.success(
                    request, 
                    f'Benvenuto nella sessione "{session.name}"! {"Carte iniziali registrate." if initial_cards else ""}'
                )
                return redirect('player_session', session_code=session_code)
                
        except Exception as e:
            from django.db import IntegrityError
            if isinstance(e, IntegrityError):
                # Errore di integrità - probabilmente personaggio già preso
                messages.error(request, f'Personaggio "{dict(Player.CHARACTERS).get(character, character)}" già selezionato da un altro giocatore.')
            else:
                logger.error(f"Errore nell'unirsi alla sessione: {e}")
                messages.error(request, 'Errore nell\'unirsi alla sessione. Riprova.')
            return self.get(request, *args, **kwargs)
    
    def _process_initial_cards(self, player, initial_cards):
        """Processa le carte iniziali selezionate dal giocatore."""
        if not initial_cards:
            return
        
        # Prima rimuovi eventuali carte già assegnate a questo giocatore
        PlayerCard.objects.filter(player=player).delete()
        
        # Processa ogni carta selezionata
        cards_processed = 0
        for card_id in initial_cards:
            try:
                # Estrai tipo e codice dalla stringa (es: "character_scarlett" -> tipo="character", codice="scarlett")
                if '_' in card_id:
                    card_type, card_code = card_id.split('_', 1)
                    
                    # Trova la carta corrispondente
                    if card_type == 'character':
                        # Per i personaggi, usa il codice del personaggio
                        character_map = {
                            'scarlett': 'scarlett',
                            'mustard': 'mustard', 
                            'white': 'white',
                            'green': 'green',
                            'peacock': 'peacock',
                            'plum': 'plum'
                        }
                        if card_code in character_map:
                            card = Card.objects.filter(
                                card_type='character', 
                                code=character_map[card_code]
                            ).first()
                    else:
                        # Per armi e stanze, usa il codice direttamente
                        card = Card.objects.filter(
                            card_type=card_type,
                            code=card_code
                        ).first()
                    
                    if card:
                        # Crea la PlayerCard
                        PlayerCard.objects.create(
                            player=player,
                            card=card,
                            has_card=True,
                            is_secret=True  # Le carte iniziali sono sempre segrete
                        )
                        cards_processed += 1
                        
                        logger.info(f"Carta iniziale assegnata: {card.name} a {player.name}")
                    else:
                        logger.warning(f"Carta non trovata: {card_type}_{card_code}")
                        
            except Exception as e:
                logger.error(f"Errore nel processare la carta {card_id}: {e}")
        
        logger.info(f"Processate {cards_processed} carte iniziali per {player.name}")


class PlayerSessionView(BaseGameView):
    """Interfaccia principale per i giocatori."""
    template_name = 'session_game.html'
    
    def dispatch(self, request, *args, **kwargs):
        session_code = self.kwargs['session_code']
        self.session = get_object_or_404(GameSession, session_code=session_code, is_active=True)
        
        # Verifica che il giocatore sia nella sessione
        player_name = request.session.get('player_name')
        if not player_name:
            messages.error(request, 'Devi unirti alla sessione prima.')
            return redirect('join_session_code', session_code=session_code)
        
        try:
            self.player = self.session.players.get(name=player_name, is_active=True)
        except Player.DoesNotExist:
            messages.error(request, 'Giocatore non trovato nella sessione.')
            return redirect('join_session_code', session_code=session_code)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ottieni tutte le carte e lo stato per questo giocatore
        all_cards = Card.objects.all().order_by('card_type', 'name')
        player_cards = {
            pc.card_id: pc for pc in 
            PlayerCard.objects.filter(player=self.player).select_related('card')
        }
        
        # Ottieni informazioni condivise da altri giocatori
        shared_cards = CardSharing.objects.filter(
            session=self.session,
            is_public=True
        ).select_related('from_player', 'card').order_by('-created_at')[:20]
        
        # Ottieni altri giocatori
        other_players = self.session.players.filter(is_active=True).exclude(id=self.player.id)
        
        context.update({
            'session': self.session,
            'session_code': self.kwargs['session_code'],
            'title': f'{self.session.name} - {self.player.name}',
            'current_player': self.player,
            'all_cards': all_cards,
            'player_cards': player_cards,
            'other_players': other_players,
            'shared_cards': shared_cards,
            'websocket_url': f'ws://{context["local_ip"]}:8000/ws/session/{self.kwargs["session_code"]}/',
        })
        return context


class SessionQRView(BaseGameView):
    """Genera codice QR per unirsi alla sessione."""
    template_name = 'session_qr.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_code = self.kwargs['session_code']
        session = get_object_or_404(GameSession, session_code=session_code)
        
        join_url = f"http://{context['local_ip']}:8000/join/{session_code}/"
        
        context.update({
            'session': session,
            'session_code': session_code,
            'join_url': join_url,
            'title': f'QR Code - {session.name}',
        })
        return context


# API Views per AJAX
class UpdatePlayerCardView(BaseGameView):
    """Aggiorna lo stato di una carta per un giocatore."""
    
    def post(self, request, session_code, player_id):
        try:
            session = get_object_or_404(GameSession, session_code=session_code)
            player = get_object_or_404(Player, id=player_id, session=session)
            
            card_id = request.POST.get('card_id')
            has_card = request.POST.get('has_card') == 'true'
            is_public = request.POST.get('is_public', 'true') == 'true'
            
            card = get_object_or_404(Card, id=card_id)
            
            player_card, created = PlayerCard.objects.get_or_create(
                player=player,
                card=card,
                defaults={'has_card': has_card, 'is_public': is_public}
            )
            
            if not created:
                player_card.has_card = has_card
                player_card.is_public = is_public
                player_card.save()
            
            # Log azione
            action = "aggiunta" if has_card else "rimossa"
            GameLog.objects.create(
                session=session,
                player=player,
                action_type='card_added' if has_card else 'card_removed',
                description=f'{player.name} ha {action} la carta {card.name}',
                data={'card_id': card.id, 'has_card': has_card, 'is_public': is_public}
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Carta {card.name} {action} con successo'
            })
            
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento carta: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class ShareCardView(BaseGameView):
    """Condividi informazioni su una carta con altri giocatori."""
    
    def post(self, request, session_code):
        try:
            session = get_object_or_404(GameSession, session_code=session_code)
            player_name = request.session.get('player_name')
            player = get_object_or_404(Player, session=session, name=player_name)
            
            card_id = request.POST.get('card_id')
            sharing_type = request.POST.get('sharing_type')
            message = request.POST.get('message', '')
            to_player_id = request.POST.get('to_player_id')
            is_public = request.POST.get('is_public') == 'true'
            
            card = get_object_or_404(Card, id=card_id)
            to_player = None
            
            if to_player_id:
                to_player = get_object_or_404(Player, id=to_player_id, session=session)
            
            # Crea condivisione
            card_share = CardSharing.objects.create(
                session=session,
                from_player=player,
                to_player=to_player,
                card=card,
                sharing_type=sharing_type,
                message=message,
                is_public=is_public,
            )
            
            # Log condivisione
            target = to_player.name if to_player else "tutti"
            GameLog.objects.create(
                session=session,
                player=player,
                action_type='card_shared',
                description=f'{player.name} ha condiviso informazioni su {card.name} con {target}',
                data={
                    'card_id': card.id,
                    'sharing_type': sharing_type,
                    'to_player_id': to_player_id,
                    'is_public': is_public,
                }
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Informazione condivisa con successo'
            })
            
        except Exception as e:
            logger.error(f"Errore nella condivisione carta: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class SessionStatsView(BaseGameView):
    """Ottieni statistiche della sessione."""
    
    def get(self, request, session_code):
        try:
            session = get_object_or_404(GameSession, session_code=session_code)
            players = session.players.filter(is_active=True)
            
            stats = {
                'session': {
                    'name': session.name,
                    'code': session.session_code,
                    'player_count': players.count(),
                    'max_players': session.max_players,
                    'created_at': session.created_at.isoformat(),
                    'is_active': session.is_active,
                    'allow_card_sharing': session.allow_card_sharing,
                },
                'players': [
                    {
                        'id': player.id,
                        'name': player.name,
                        'character': player.get_character_display(),
                        'is_host': player.is_host,
                        'cards_count': player.cards.filter(has_card=True).count(),
                        'public_cards_count': player.cards.filter(
                            has_card=True, is_public=True
                        ).count(),
                        'joined_at': player.joined_at.isoformat(),
                    }
                    for player in players
                ],
                'cards': {
                    'total': Card.objects.count(),
                    'characters': Card.objects.filter(card_type='character').count(),
                    'weapons': Card.objects.filter(card_type='weapon').count(),
                    'rooms': Card.objects.filter(card_type='room').count(),
                },
                'activity': {
                    'recent_shares': CardSharing.objects.filter(
                        session=session
                    ).count(),
                    'total_logs': session.logs.count(),
                }
            }
            
            return JsonResponse(stats)
            
        except Exception as e:
            logger.error(f"Errore nel recupero statistiche: {e}")
            return JsonResponse({'error': str(e)}, status=400)


class ConnectionInfoView(BaseGameView):
    """Ottieni informazioni di connessione per dispositivi mobili."""
    
    def get(self, request):
        local_ip = self.get_local_ip()
        
        info = {
            'local_ip': local_ip,
            'host_url': f'http://localhost:8000/',
            'join_url': f'http://{local_ip}:8000/join/',
            'api_url': f'http://{local_ip}:8000/api/',
            'websocket_url': f'ws://{local_ip}:8000/ws/',
            'active_sessions': GameSession.objects.filter(is_active=True).count(),
        }
        
        return JsonResponse(info)


# Viste di utilità
class AboutView(TemplateView):
    """Pagina informativa su come usare l'applicazione."""
    template_name = 'about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Come Funziona - Cluedo Tracker'
        return context


class OfflineView(TemplateView):
    """Pagina offline per PWA."""
    template_name = 'offline.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Offline - Cluedo Tracker'
        return context


from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST


@method_decorator(require_POST, name='dispatch')
class EndSessionView(View):
    def post(self, request, session_code):
        session = get_object_or_404(GameSession, session_code=session_code, is_active=True)
        # Elimina anche i giocatori, le carte, le condivisioni e i log collegati
        PlayerCard.objects.filter(player__session=session).delete()
        session.players.all().delete()
        session.card_shares.all().delete()
        session.logs.all().delete()
        session.delete()  # Elimina la sessione stessa dal DB
        return JsonResponse({'success': True, 'message': 'Sessione e dati eliminati dal database'})