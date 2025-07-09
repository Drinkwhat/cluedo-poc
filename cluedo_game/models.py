from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import socket
import random
import string


class GameSession(models.Model):
    """
    Rappresenta una sessione di gioco Cluedo che i giocatori possono unirsi.
    Gestisce la rete locale e la condivisione delle carte.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name="Nome Sessione")
    session_code = models.CharField(max_length=6, unique=True, verbose_name="Codice Sessione")
    host_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Host")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Attiva")
    max_players = models.IntegerField(default=6, verbose_name="Max Giocatori")
    
    # Configurazioni per condivisione carte
    allow_card_sharing = models.BooleanField(default=True, verbose_name="Permetti Condivisione Carte")
    auto_reveal_cards = models.BooleanField(default=False, verbose_name="Rivela Carte Automaticamente")
    
    class Meta:
        verbose_name = "Sessione di Gioco"
        verbose_name_plural = "Sessioni di Gioco"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.session_code})"
    
    def save(self, *args, **kwargs):
        if not self.session_code:
            self.session_code = self.generate_session_code()
        if not self.host_ip:
            self.host_ip = self.get_local_ip()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_session_code():
        """Genera un codice sessione unico."""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not GameSession.objects.filter(session_code=code).exists():
                return code
    
    @staticmethod
    def get_local_ip():
        """Ottieni l'indirizzo IP locale della macchina."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    @property
    def player_count(self):
        return self.players.filter(is_active=True).count()
    
    @property
    def mobile_url(self):
        return f"http://{self.host_ip}:8000/join/{self.session_code}/"
    
    @property
    def qr_url(self):
        return f"http://{self.host_ip}:8000/qr/{self.session_code}/"


class Player(models.Model):
    """
    Rappresenta un giocatore in una sessione di gioco.
    Gestisce il personaggio scelto e le carte possedute.
    """
    
    CHARACTERS = [
        ('colonel_mustard', 'Colonnello Mustard'),
        ('miss_scarlett', 'Miss Scarlett'),
        ('professor_plum', 'Professor Plum'),
        ('mrs_peacock', 'Mrs. Peacock'),
        ('mr_green', 'Mr. Green'),
        ('mrs_white', 'Mrs. White'),
    ]
    
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='players')
    name = models.CharField(max_length=50, verbose_name="Nome Giocatore")
    character = models.CharField(max_length=20, choices=CHARACTERS, verbose_name="Personaggio")
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name="Attivo")
    is_host = models.BooleanField(default=False, verbose_name="È Host")
    personal_notes = models.TextField(blank=True, verbose_name="Note Personali")
    
    # Configurazioni privacy
    share_cards_publicly = models.BooleanField(default=True, verbose_name="Condividi Carte Pubblicamente")
    
    class Meta:
        verbose_name = "Giocatore"
        verbose_name_plural = "Giocatori"
        unique_together = ['session', 'character']
        ordering = ['joined_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_character_display()})"
    
    @property
    def character_display(self):
        return self.get_character_display()
    
    @property
    def cards_count(self):
        return self.cards.filter(has_card=True).count()


class Card(models.Model):
    """
    Rappresenta una carta del gioco Cluedo.
    Include personaggi, armi e stanze.
    """
    
    CARD_TYPES = [
        ('character', 'Personaggio'),
        ('weapon', 'Arma'),
        ('room', 'Stanza'),
    ]
    
    name = models.CharField(max_length=50, verbose_name="Nome Carta")
    card_type = models.CharField(max_length=20, choices=CARD_TYPES, verbose_name="Tipo Carta")
    code = models.CharField(max_length=30, unique=True, verbose_name="Codice Carta")
    icon = models.CharField(max_length=50, default="fas fa-question", verbose_name="Icona FontAwesome")
    description = models.TextField(blank=True, verbose_name="Descrizione")
    
    class Meta:
        verbose_name = "Carta"
        verbose_name_plural = "Carte"
        ordering = ['card_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_card_type_display()})"


class PlayerCard(models.Model):
    """
    Collega i giocatori alle loro carte.
    Gestisce il possesso delle carte e la condivisione.
    """
    
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='cards')
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    has_card = models.BooleanField(default=False, verbose_name="Ha la Carta")
    is_public = models.BooleanField(default=True, verbose_name="Visibile ad Altri")
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Carta Giocatore"
        verbose_name_plural = "Carte Giocatori"
        unique_together = ['player', 'card']
    
    def __str__(self):
        status = "Ha" if self.has_card else "Non ha"
        visibility = "(Pubblico)" if self.is_public else "(Privato)"
        return f"{self.player.name} {status} {self.card.name} {visibility}"


class CardKnowledge(models.Model):
    """
    Traccia cosa sanno i giocatori sulle carte degli altri giocatori.
    Sistema di deduzione e condivisione informazioni.
    """
    
    KNOWLEDGE_TYPES = [
        ('has', 'Ha la carta'),
        ('not_has', 'Non ha la carta'),
        ('unknown', 'Sconosciuto'),
        ('maybe', 'Forse ha'),
        ('probably_not', 'Probabilmente non ha'),
    ]
    
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='knowledge')
    target_player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='known_by')
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    knowledge_type = models.CharField(max_length=15, choices=KNOWLEDGE_TYPES, default='unknown')
    confidence = models.IntegerField(default=50, help_text="Livello di confidenza (0-100)")
    notes = models.TextField(blank=True, verbose_name="Note sulla Deduzione")
    is_shared = models.BooleanField(default=False, verbose_name="Condiviso con Altri")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Conoscenza Carta"
        verbose_name_plural = "Conoscenze Carte"
        unique_together = ['player', 'target_player', 'card']
    
    def __str__(self):
        return f"{self.player.name} sa che {self.target_player.name} {self.get_knowledge_type_display()} {self.card.name}"


class CardSharing(models.Model):
    """
    Gestisce la condivisione di informazioni sulle carte tra giocatori.
    """
    
    SHARING_TYPES = [
        ('reveal', 'Rivela Carta'),
        ('hint', 'Suggerimento'),
        ('question', 'Domanda'),
        ('deduction', 'Deduzione'),
    ]
    
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='card_shares')
    from_player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='shared_from')
    to_player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='shared_to', null=True, blank=True)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    sharing_type = models.CharField(max_length=15, choices=SHARING_TYPES)
    message = models.TextField(verbose_name="Messaggio")
    is_public = models.BooleanField(default=False, verbose_name="Visibile a Tutti")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Condivisione Carta"
        verbose_name_plural = "Condivisioni Carte"
        ordering = ['-created_at']
    
    def __str__(self):
        target = self.to_player.name if self.to_player else "Tutti"
        return f"{self.from_player.name} -> {target}: {self.get_sharing_type_display()} {self.card.name}"


class GameLog(models.Model):
    """
    Log degli eventi del gioco per tracciare le azioni.
    """
    
    ACTION_TYPES = [
        ('player_joined', 'Giocatore si è unito'),
        ('player_left', 'Giocatore è uscito'),
        ('card_added', 'Carta aggiunta'),
        ('card_removed', 'Carta rimossa'),
        ('card_shared', 'Carta condivisa'),
        ('knowledge_updated', 'Conoscenza aggiornata'),
        ('note_added', 'Nota aggiunta'),
        ('session_created', 'Sessione creata'),
        ('session_ended', 'Sessione terminata'),
    ]
    
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='logs')
    player = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    description = models.TextField(verbose_name="Descrizione")
    data = models.JSONField(default=dict, blank=True, verbose_name="Dati Extra")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Log di Gioco"
        verbose_name_plural = "Log di Gioco"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.session.session_code}: {self.get_action_type_display()}"


# Funzione per inizializzare le carte standard del Cluedo
def initialize_cluedo_cards():
    """
    Inizializza tutte le carte standard del Cluedo nel database.
    """
    
    # Personaggi
    characters = [
        ('colonel_mustard', 'Colonnello Mustard', 'fas fa-user-tie'),
        ('miss_scarlett', 'Miss Scarlett', 'fas fa-female'),
        ('professor_plum', 'Professor Plum', 'fas fa-graduation-cap'),
        ('mrs_peacock', 'Mrs. Peacock', 'fas fa-crown'),
        ('mr_green', 'Mr. Green', 'fas fa-male'),
        ('mrs_white', 'Mrs. White', 'fas fa-user-nurse'),
    ]
    
    # Armi
    weapons = [
        ('candlestick', 'Candelabro', 'fas fa-fire'),
        ('knife', 'Coltello', 'fas fa-knife-kitchen'),
        ('lead_pipe', 'Tubo di Piombo', 'fas fa-pipe'),
        ('revolver', 'Rivoltella', 'fas fa-gun'),
        ('rope', 'Corda', 'fas fa-rope'),
        ('wrench', 'Chiave Inglese', 'fas fa-wrench'),
    ]
    
    # Stanze
    rooms = [
        ('kitchen', 'Cucina', 'fas fa-utensils'),
        ('ballroom', 'Sala da Ballo', 'fas fa-music'),
        ('conservatory', 'Serra', 'fas fa-seedling'),
        ('dining_room', 'Sala da Pranzo', 'fas fa-chair'),
        ('billiard_room', 'Sala Biliardo', 'fas fa-circle'),
        ('library', 'Biblioteca', 'fas fa-book'),
        ('lounge', 'Salotto', 'fas fa-couch'),
        ('hall', 'Atrio', 'fas fa-door-open'),
        ('study', 'Studio', 'fas fa-desk'),
    ]
    
    # Crea le carte
    for code, name, icon in characters:
        Card.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'card_type': 'character',
                'icon': icon,
                'description': f'Personaggio: {name}'
            }
        )
    
    for code, name, icon in weapons:
        Card.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'card_type': 'weapon',
                'icon': icon,
                'description': f'Arma: {name}'
            }
        )
    
    for code, name, icon in rooms:
        Card.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'card_type': 'room',
                'icon': icon,
                'description': f'Stanza: {name}'
            }
        )