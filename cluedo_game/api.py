from ninja import Router, Schema, Field
from ninja.pagination import paginate
from typing import List, Optional
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from pydantic import validator
import logging

from .models import (
    GameSession, Player, Card, PlayerCard, 
    CardKnowledge, CardSharing, GameLog,
    initialize_cluedo_cards
)

logger = logging.getLogger(__name__)

# Schemas per serializzazione API
class GameSessionSchema(Schema):
    id: str
    name: str
    session_code: str
    host_ip: Optional[str] = None
    created_at: str
    is_active: bool
    max_players: int
    player_count: int
    allow_card_sharing: bool
    auto_reveal_cards: bool
    mobile_url: str

class PlayerSchema(Schema):
    id: int
    name: str
    character: str
    character_display: str
    joined_at: str
    is_active: bool
    is_host: bool
    cards_count: int
    personal_notes: str = ""

class CardSchema(Schema):
    id: int
    name: str
    card_type: str
    code: str
    icon: str
    description: str = ""

class PlayerCardSchema(Schema):
    id: int
    card: CardSchema
    has_card: bool
    is_public: bool
    updated_at: str

class CardSharingSchema(Schema):
    id: int
    from_player_name: str
    to_player_name: Optional[str] = None
    card_name: str
    sharing_type: str
    message: str
    is_public: bool
    created_at: str

class GameLogSchema(Schema):
    id: int
    action_type: str
    description: str
    player_name: Optional[str] = None
    created_at: str

# Input schemas
class CreateSessionSchema(Schema):
    name: str = Field(..., min_length=1, max_length=100)
    max_players: int = Field(default=6, ge=2, le=10)
    allow_card_sharing: bool = Field(default=True)
    auto_reveal_cards: bool = Field(default=False)

class JoinSessionSchema(Schema):
    session_code: str = Field(..., min_length=6, max_length=6)
    player_name: str = Field(..., min_length=1, max_length=50)
    character: str

class UpdatePlayerCardSchema(Schema):
    card_id: int
    has_card: bool
    is_public: bool = Field(default=True)

class ShareCardSchema(Schema):
    card_id: int
    sharing_type: str
    message: str = ""
    to_player_id: Optional[int] = None
    is_public: bool = Field(default=True)

class UpdateNotesSchema(Schema):
    notes: str

# Inizializza router
router = Router()

# ====== ENDPOINTS DI CONNESSIONE ======

@router.get("/connection-info/", response=dict)
def get_connection_info(request):
    """Ottieni informazioni di connessione per dispositivi mobili."""
    local_ip = GameSession.get_local_ip()
    
    return {
        'local_ip': local_ip,
        'host_url': f'http://localhost:8000/',
        'join_url': f'http://{local_ip}:8000/join/',
        'api_url': f'http://{local_ip}:8000/api/',
        'websocket_url': f'ws://{local_ip}:8000/ws/',
        'docs_url': f'http://{local_ip}:8000/api/docs/',
        'active_sessions': GameSession.objects.filter(is_active=True).count(),
        'timestamp': timezone.now().isoformat(),
    }

# ====== ENDPOINTS SESSIONI ======

@router.get("/sessions/", response=List[GameSessionSchema])
@paginate
def list_sessions(request, active_only: bool = True):
    """Ottieni lista delle sessioni di gioco."""
    sessions = GameSession.objects.all()
    if active_only:
        sessions = sessions.filter(is_active=True)
    
    return [
        GameSessionSchema(
            id=str(session.id),
            name=session.name,
            session_code=session.session_code,
            host_ip=session.host_ip,
            created_at=session.created_at.isoformat(),
            is_active=session.is_active,
            max_players=session.max_players,
            player_count=session.player_count,
            allow_card_sharing=session.allow_card_sharing,
            auto_reveal_cards=session.auto_reveal_cards,
            mobile_url=session.mobile_url,
        )
        for session in sessions
    ]

@router.post("/sessions/", response=GameSessionSchema)
def create_session(request, payload: CreateSessionSchema):
    """Crea una nuova sessione di gioco."""
    
    # Inizializza le carte se non esistono
    if not Card.objects.exists():
        initialize_cluedo_cards()
        logger.info("Carte Cluedo inizializzate automaticamente")
    
    session = GameSession.objects.create(
        name=payload.name,
        max_players=payload.max_players,
        allow_card_sharing=payload.allow_card_sharing,
        auto_reveal_cards=payload.auto_reveal_cards,
    )
    
    # Log creazione sessione
    GameLog.objects.create(
        session=session,
        action_type='session_created',
        description=f'Sessione "{session.name}" creata via API',
        data={
            'session_code': session.session_code,
            'max_players': session.max_players,
            'host_ip': session.host_ip,
            'allow_card_sharing': session.allow_card_sharing,
        }
    )
    
    return GameSessionSchema(
        id=str(session.id),
        name=session.name,
        session_code=session.session_code,
        host_ip=session.host_ip,
        created_at=session.created_at.isoformat(),
        is_active=session.is_active,
        max_players=session.max_players,
        player_count=session.player_count,
        allow_card_sharing=session.allow_card_sharing,
        auto_reveal_cards=session.auto_reveal_cards,
        mobile_url=session.mobile_url,
    )

@router.get("/sessions/{session_code}/", response=GameSessionSchema)
def get_session(request, session_code: str):
    """Ottieni una sessione specifica tramite codice."""
    session = get_object_or_404(GameSession, session_code=session_code.upper())
    
    return GameSessionSchema(
        id=str(session.id),
        name=session.name,
        session_code=session.session_code,
        host_ip=session.host_ip,
        created_at=session.created_at.isoformat(),
        is_active=session.is_active,
        max_players=session.max_players,
        player_count=session.player_count,
        allow_card_sharing=session.allow_card_sharing,
        auto_reveal_cards=session.auto_reveal_cards,
        mobile_url=session.mobile_url,
    )

@router.delete("/sessions/{session_code}/")
def deactivate_session(request, session_code: str):
    """Disattiva una sessione."""
    session = get_object_or_404(GameSession, session_code=session_code.upper())
    session.is_active = False
    session.save()
    
    GameLog.objects.create(
        session=session,
        action_type='session_ended',
        description='Sessione terminata via API',
    )
    
    return {"message": "Sessione disattivata con successo"}

# ====== ENDPOINTS GIOCATORI ======

@router.get("/sessions/{session_code}/players/", response=List[PlayerSchema])
def list_players(request, session_code: str):
    """Ottieni giocatori in una sessione."""
    session = get_object_or_404(GameSession, session_code=session_code.upper())
    players = session.players.filter(is_active=True)
    
    return [
        PlayerSchema(
            id=player.id,
            name=player.name,
            character=player.character,
            character_display=player.get_character_display(),
            joined_at=player.joined_at.isoformat(),
            is_active=player.is_active,
            is_host=player.is_host,
            cards_count=player.cards_count,
            personal_notes=player.personal_notes,
        )
        for player in players
    ]

@router.post("/sessions/{session_code}/players/", response=PlayerSchema)
def join_session(request, session_code: str, payload: JoinSessionSchema):
    """Unisciti a una sessione come giocatore."""
    session = get_object_or_404(GameSession, session_code=session_code.upper(), is_active=True)
    
    # Valida codice sessione
    if payload.session_code.upper() != session_code.upper():
        return {"error": "Codice sessione non corrispondente"}, 400
    
    # Controlla se il personaggio è disponibile
    if session.players.filter(character=payload.character, is_active=True).exists():
        return {"error": "Personaggio già selezionato"}, 400
    
    # Controlla numero massimo giocatori
    if session.player_count >= session.max_players:
        return {"error": "Sessione piena"}, 400
    
    # Crea o aggiorna giocatore
    with transaction.atomic():
        player, created = Player.objects.get_or_create(
            session=session,
            name=payload.player_name,
            defaults={'character': payload.character, 'is_active': True}
        )
        
        if not created:
            player.character = payload.character
            player.is_active = True
            player.save()
        
        # Log ingresso giocatore
        GameLog.objects.create(
            session=session,
            player=player,
            action_type='player_joined',
            description=f'{player.name} si è unito come {player.get_character_display()} via API',
            data={'character': payload.character, 'created': created}
        )
    
    return PlayerSchema(
        id=player.id,
        name=player.name,
        character=player.character,
        character_display=player.get_character_display(),
        joined_at=player.joined_at.isoformat(),
        is_active=player.is_active,
        is_host=player.is_host,
        cards_count=player.cards_count,
        personal_notes=player.personal_notes,
    )

# ====== ENDPOINTS CARTE ======

@router.get("/cards/", response=List[CardSchema])
def list_cards(request, card_type: Optional[str] = None):
    """Ottieni tutte le carte di gioco."""
    
    # Inizializza le carte se non esistono
    if not Card.objects.exists():
        initialize_cluedo_cards()
        logger.info("Carte Cluedo inizializzate automaticamente")
    
    cards = Card.objects.all().order_by('card_type', 'name')
    if card_type:
        cards = cards.filter(card_type=card_type)
    
    return [
        CardSchema(
            id=card.id,
            name=card.name,
            card_type=card.card_type,
            code=card.code,
            icon=card.icon,
            description=card.description,
        )
        for card in cards
    ]

@router.get("/sessions/{session_code}/players/{player_id}/cards/", response=List[PlayerCardSchema])
def get_player_cards(request, session_code: str, player_id: int):
    """Ottieni le carte di un giocatore."""
    session = get_object_or_404(GameSession, session_code=session_code.upper())
    player = get_object_or_404(Player, id=player_id, session=session)
    
    player_cards = PlayerCard.objects.filter(player=player).select_related('card')
    
    return [
        PlayerCardSchema(
            id=pc.id,
            card=CardSchema(
                id=pc.card.id,
                name=pc.card.name,
                card_type=pc.card.card_type,
                code=pc.card.code,
                icon=pc.card.icon,
                description=pc.card.description,
            ),
            has_card=pc.has_card,
            is_public=pc.is_public,
            updated_at=pc.updated_at.isoformat(),
        )
        for pc in player_cards
    ]

@router.put("/sessions/{session_code}/players/{player_id}/cards/")
def update_player_card(request, session_code: str, player_id: int, payload: UpdatePlayerCardSchema):
    """Aggiorna lo stato di una carta di un giocatore."""
    session = get_object_or_404(GameSession, session_code=session_code.upper())
    player = get_object_or_404(Player, id=player_id, session=session)
    card = get_object_or_404(Card, id=payload.card_id)
    
    with transaction.atomic():
        player_card, created = PlayerCard.objects.get_or_create(
            player=player,
            card=card,
            defaults={'has_card': payload.has_card, 'is_public': payload.is_public}
        )
        
        if not created:
            player_card.has_card = payload.has_card
            player_card.is_public = payload.is_public
            player_card.save()
        
        # Log aggiornamento carta
        action = "aggiunta" if payload.has_card else "rimossa"
        GameLog.objects.create(
            session=session,
            player=player,
            action_type='card_added' if payload.has_card else 'card_removed',
            description=f'{player.name} ha {action} la carta {card.name} via API',
            data={
                'card_id': card.id,
                'has_card': payload.has_card,
                'is_public': payload.is_public,
                'created': created,
            }
        )
    
    return {"message": f"Carta {card.name} aggiornata con successo"}

# ====== ENDPOINTS CONDIVISIONE CARTE ======

@router.post("/sessions/{session_code}/share-card/")
def share_card(request, session_code: str, payload: ShareCardSchema):
    """Condividi informazioni su una carta con altri giocatori."""
    session = get_object_or_404(GameSession, session_code=session_code.upper())
    
    # Per semplicità, utilizziamo il primo player se non specificato
    # In un'implementazione reale, useresti l'autenticazione
    from_player = session.players.filter(is_active=True).first()
    if not from_player:
        return {"error": "Nessun giocatore attivo nella sessione"}, 400
    
    card = get_object_or_404(Card, id=payload.card_id)
    to_player = None
    
    if payload.to_player_id:
        to_player = get_object_or_404(Player, id=payload.to_player_id, session=session)
    
    # Crea condivisione
    card_share = CardSharing.objects.create(
        session=session,
        from_player=from_player,
        to_player=to_player,
        card=card,
        sharing_type=payload.sharing_type,
        message=payload.message,
        is_public=payload.is_public,
    )
    
    # Log condivisione
    target = to_player.name if to_player else "tutti"
    GameLog.objects.create(
        session=session,
        player=from_player,
        action_type='card_shared',
        description=f'{from_player.name} ha condiviso informazioni su {card.name} con {target} via API',
        data={
            'card_id': card.id,
            'sharing_type': payload.sharing_type,
            'to_player_id': payload.to_player_id,
            'is_public': payload.is_public,
        }
    )
    
    return {"message": "Informazione condivisa con successo"}

@router.get("/sessions/{session_code}/shared-cards/", response=List[CardSharingSchema])
@paginate
def get_shared_cards(request, session_code: str, public_only: bool = True):
    """Ottieni carte condivise in una sessione."""
    session = get_object_or_404(GameSession, session_code=session_code.upper())
    
    shared_cards = CardSharing.objects.filter(session=session)
    if public_only:
        shared_cards = shared_cards.filter(is_public=True)
    
    shared_cards = shared_cards.select_related('from_player', 'to_player', 'card').order_by('-created_at')
    
    return [
        CardSharingSchema(
            id=share.id,
            from_player_name=share.from_player.name,
            to_player_name=share.to_player.name if share.to_player else None,
            card_name=share.card.name,
            sharing_type=share.sharing_type,
            message=share.message,
            is_public=share.is_public,
            created_at=share.created_at.isoformat(),
        )
        for share in shared_cards
    ]

# ====== ENDPOINTS NOTE ======

@router.put("/sessions/{session_code}/players/{player_id}/notes/")
def update_player_notes(request, session_code: str, player_id: int, payload: UpdateNotesSchema):
    """Aggiorna le note personali di un giocatore."""
    session = get_object_or_404(GameSession, session_code=session_code.upper())
    player = get_object_or_404(Player, id=player_id, session=session)
    
    player.personal_notes = payload.notes
    player.save()
    
    # Log aggiornamento note
    GameLog.objects.create(
        session=session,
        player=player,
        action_type='note_added',
        description=f'{player.name} ha aggiornato le note personali via API',
        data={'notes_length': len(payload.notes)}
    )
    
    return {"message": "Note aggiornate con successo"}

# ====== ENDPOINTS LOG E STATISTICHE ======

@router.get("/sessions/{session_code}/logs/", response=List[GameLogSchema])
@paginate
def get_session_logs(request, session_code: str):
    """Ottieni log di una sessione."""
    session = get_object_or_404(GameSession, session_code=session_code.upper())
    logs = GameLog.objects.filter(session=session).select_related('player').order_by('-created_at')
    
    return [
        GameLogSchema(
            id=log.id,
            action_type=log.action_type,
            description=log.description,
            player_name=log.player.name if log.player else None,
            created_at=log.created_at.isoformat(),
        )
        for log in logs
    ]

@router.get("/sessions/{session_code}/stats/")
def get_session_stats(request, session_code: str):
    """Ottieni statistiche dettagliate della sessione."""
    session = get_object_or_404(GameSession, session_code=session_code.upper())
    
    players = session.players.filter(is_active=True)
    total_cards = Card.objects.count()
    
    stats = {
        'session': {
            'name': session.name,
            'code': session.session_code,
            'created_at': session.created_at.isoformat(),
            'player_count': players.count(),
            'max_players': session.max_players,
            'is_active': session.is_active,
            'allow_card_sharing': session.allow_card_sharing,
            'auto_reveal_cards': session.auto_reveal_cards,
            'host_ip': session.host_ip,
        },
        'players': [
            {
                'id': player.id,
                'name': player.name,
                'character': player.get_character_display(),
                'is_host': player.is_host,
                'cards_count': PlayerCard.objects.filter(player=player, has_card=True).count(),
                'public_cards_count': PlayerCard.objects.filter(
                    player=player, has_card=True, is_public=True
                ).count(),
                'private_cards_count': PlayerCard.objects.filter(
                    player=player, has_card=True, is_public=False
                ).count(),
                'joined_at': player.joined_at.isoformat(),
            }
            for player in players
        ],
        'cards': {
            'total': total_cards,
            'characters': Card.objects.filter(card_type='character').count(),
            'weapons': Card.objects.filter(card_type='weapon').count(),
            'rooms': Card.objects.filter(card_type='room').count(),
        },
        'activity': {
            'total_shares': CardSharing.objects.filter(session=session).count(),
            'public_shares': CardSharing.objects.filter(session=session, is_public=True).count(),
            'total_logs': session.logs.count(),
            'cards_in_play': PlayerCard.objects.filter(
                player__session=session, has_card=True
            ).count(),
        },
        'sharing': {
            'is_enabled': session.allow_card_sharing,
            'auto_reveal': session.auto_reveal_cards,
            'recent_shares': CardSharing.objects.filter(
                session=session, 
                created_at__gte=timezone.now() - timezone.timedelta(hours=1)
            ).count(),
        }
    }
    
    return stats

# ====== ENDPOINTS UTILITY ======

@router.post("/initialize-cards/")
def initialize_cards_endpoint(request):
    """Inizializza le carte standard del Cluedo nel database."""
    try:
        before_count = Card.objects.count()
        initialize_cluedo_cards()
        after_count = Card.objects.count()
        
        return {
            'message': 'Carte inizializzate con successo',
            'cards_before': before_count,
            'cards_after': after_count,
            'cards_added': after_count - before_count,
        }
    except Exception as e:
        logger.error(f"Errore nell'inizializzazione carte: {e}")
        return {"error": str(e)}, 500

@router.get("/health/")
def health_check(request):
    """Controllo stato dell'applicazione."""
    return {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'total_sessions': GameSession.objects.count(),
        'active_sessions': GameSession.objects.filter(is_active=True).count(),
        'total_players': Player.objects.filter(is_active=True).count(),
        'total_cards': Card.objects.count(),
    }
