import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)


class SessionConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer per aggiornamenti in tempo reale delle sessioni.
    Gestisce la comunicazione tra giocatori nella stessa sessione.
    """

    async def connect(self):
        self.session_code = self.scope['url_route']['kwargs']['session_code']
        self.session_group_name = f'session_{self.session_code}'

        # Verifica che la sessione esista
        session_exists = await self.check_session_exists(self.session_code)
        if not session_exists:
            await self.close()
            return

        # Unisciti al gruppo della sessione
        await self.channel_layer.group_add(
            self.session_group_name,
            self.channel_name
        )

        await self.accept()
        
        # Invia messaggio di benvenuto
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': f'Connesso alla sessione {self.session_code}',
            'session_code': self.session_code
        }))

        logger.info(f"WebSocket connesso alla sessione {self.session_code}")

    async def disconnect(self, close_code):
        # Lascia il gruppo della sessione
        await self.channel_layer.group_discard(
            self.session_group_name,
            self.channel_name
        )
        
        logger.info(f"WebSocket disconnesso dalla sessione {self.session_code}")

    async def receive(self, text_data):
        """Ricevi messaggio dal WebSocket."""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'message')
            
            if message_type == 'card_update':
                await self.handle_card_update(text_data_json)
            elif message_type == 'card_share':
                await self.handle_card_share(text_data_json)
            elif message_type == 'player_joined':
                await self.handle_player_joined(text_data_json)
            elif message_type == 'player_left':
                await self.handle_player_left(text_data_json)
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': text_data_json.get('timestamp')
                }))
            else:
                # Messaggi generici
                await self.channel_layer.group_send(
                    self.session_group_name,
                    {
                        'type': 'session_message',
                        'data': text_data_json
                    }
                )
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Formato JSON non valido'
            }))
        except Exception as e:
            logger.error(f"Errore in WebSocket receive: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Errore nel processare il messaggio'
            }))

    async def handle_card_update(self, data):
        """Gestisce aggiornamenti alle carte dei giocatori."""
        player_name = data.get('player_name')
        card_name = data.get('card_name')
        has_card = data.get('has_card')
        is_public = data.get('is_public', True)
        
        if not all([player_name, card_name]) or has_card is None:
            return
        
        # Invia aggiornamento a tutti nella sessione
        await self.channel_layer.group_send(
            self.session_group_name,
            {
                'type': 'card_update_notification',
                'player_name': player_name,
                'card_name': card_name,
                'has_card': has_card,
                'is_public': is_public,
                'timestamp': data.get('timestamp')
            }
        )

    async def handle_card_share(self, data):
        """Gestisce condivisione di informazioni sulle carte."""
        from_player = data.get('from_player')
        to_player = data.get('to_player')  # None se pubblico
        card_name = data.get('card_name')
        sharing_type = data.get('sharing_type')
        message = data.get('message', '')
        
        if not all([from_player, card_name, sharing_type]):
            return
        
        # Invia notifica di condivisione
        await self.channel_layer.group_send(
            self.session_group_name,
            {
                'type': 'card_share_notification',
                'from_player': from_player,
                'to_player': to_player,
                'card_name': card_name,
                'sharing_type': sharing_type,
                'message': message,
                'timestamp': data.get('timestamp')
            }
        )

    async def handle_player_joined(self, data):
        """Gestisce l'ingresso di un nuovo giocatore."""
        player_name = data.get('player_name')
        character = data.get('character')
        
        if not all([player_name, character]):
            return
        
        await self.channel_layer.group_send(
            self.session_group_name,
            {
                'type': 'player_joined_notification',
                'player_name': player_name,
                'character': character,
                'timestamp': data.get('timestamp')
            }
        )

    async def handle_player_left(self, data):
        """Gestisce l'uscita di un giocatore."""
        player_name = data.get('player_name')
        
        if not player_name:
            return
        
        await self.channel_layer.group_send(
            self.session_group_name,
            {
                'type': 'player_left_notification',
                'player_name': player_name,
                'timestamp': data.get('timestamp')
            }
        )

    # Handlers per i messaggi dal gruppo
    async def session_message(self, event):
        """Invia messaggio generico alla sessione."""
        await self.send(text_data=json.dumps(event['data']))

    async def card_update_notification(self, event):
        """Invia notifica di aggiornamento carta."""
        await self.send(text_data=json.dumps({
            'type': 'card_update',
            'player_name': event['player_name'],
            'card_name': event['card_name'],
            'has_card': event['has_card'],
            'is_public': event['is_public'],
            'timestamp': event['timestamp']
        }))

    async def card_share_notification(self, event):
        """Invia notifica di condivisione carta."""
        await self.send(text_data=json.dumps({
            'type': 'card_share',
            'from_player': event['from_player'],
            'to_player': event['to_player'],
            'card_name': event['card_name'],
            'sharing_type': event['sharing_type'],
            'message': event['message'],
            'timestamp': event['timestamp']
        }))

    async def player_joined_notification(self, event):
        """Invia notifica di giocatore entrato."""
        await self.send(text_data=json.dumps({
            'type': 'player_joined',
            'player_name': event['player_name'],
            'character': event['character'],
            'timestamp': event['timestamp']
        }))

    async def player_left_notification(self, event):
        """Invia notifica di giocatore uscito."""
        await self.send(text_data=json.dumps({
            'type': 'player_left',
            'player_name': event['player_name'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def check_session_exists(self, session_code):
        """Controlla se la sessione esiste ed è attiva."""
        from .models import GameSession
        try:
            GameSession.objects.get(session_code=session_code, is_active=True)
            return True
        except ObjectDoesNotExist:
            return False


class GeneralConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer per comunicazione generale.
    Per notifiche globali e aggiornamenti del sistema.
    """

    async def connect(self):
        self.group_name = 'general_updates'

        # Unisciti al gruppo generale
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connesso agli aggiornamenti generali'
        }))

        logger.info("WebSocket connesso al canale generale")

    async def disconnect(self, close_code):
        # Lascia il gruppo generale
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        
        logger.info("WebSocket disconnesso dal canale generale")

    async def receive(self, text_data):
        """Ricevi messaggio dal WebSocket generale."""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'message')
            
            if message_type == 'get_sessions':
                await self.send_active_sessions()
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': text_data_json.get('timestamp')
                }))
            else:
                # Messaggi generici - ritrasmetti a tutti
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'general_message',
                        'data': text_data_json
                    }
                )
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Formato JSON non valido'
            }))
        except Exception as e:
            logger.error(f"Errore in WebSocket generale receive: {e}")

    async def send_active_sessions(self):
        """Invia lista delle sessioni attive."""
        sessions = await self.get_active_sessions()
        await self.send(text_data=json.dumps({
            'type': 'active_sessions',
            'sessions': sessions
        }))

    async def general_message(self, event):
        """Invia messaggio generale."""
        await self.send(text_data=json.dumps(event['data']))

    @database_sync_to_async
    def get_active_sessions(self):
        """Ottieni lista delle sessioni attive."""
        from .models import GameSession
        sessions = GameSession.objects.filter(is_active=True).values(
            'session_code', 'name', 'player_count', 'max_players', 'created_at'
        )
        return list(sessions)
