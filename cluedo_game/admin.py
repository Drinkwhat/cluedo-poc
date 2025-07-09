from django.contrib import admin
from .models import GameSession, Player, Card, PlayerCard, CardKnowledge, CardSharing, GameLog


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'session_code', 'player_count', 'max_players', 'is_active', 'created_at']
    list_filter = ['is_active', 'allow_card_sharing', 'auto_reveal_cards', 'created_at']
    search_fields = ['name', 'session_code']
    readonly_fields = ['id', 'session_code', 'host_ip', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informazioni Base', {
            'fields': ('name', 'session_code', 'host_ip')
        }),
        ('Configurazione', {
            'fields': ('max_players', 'allow_card_sharing', 'auto_reveal_cards', 'is_active')
        }),
        ('Timestamp', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['name', 'character', 'session', 'is_host', 'is_active', 'cards_count', 'joined_at']
    list_filter = ['character', 'is_host', 'is_active', 'joined_at']
    search_fields = ['name', 'session__name', 'session__session_code']
    
    def cards_count(self, obj):
        return obj.cards.filter(has_card=True).count()
    cards_count.short_description = 'Carte Possedute'


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ['name', 'card_type', 'code', 'icon']
    list_filter = ['card_type']
    search_fields = ['name', 'code']
    ordering = ['card_type', 'name']
    
    fieldsets = (
        ('Informazioni Carta', {
            'fields': ('name', 'card_type', 'code')
        }),
        ('Visualizzazione', {
            'fields': ('icon', 'description')
        }),
    )


@admin.register(PlayerCard)
class PlayerCardAdmin(admin.ModelAdmin):
    list_display = ['player', 'card', 'has_card', 'is_public', 'updated_at']
    list_filter = ['has_card', 'is_public', 'card__card_type', 'updated_at']
    search_fields = ['player__name', 'card__name']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('player', 'card')


@admin.register(CardKnowledge)
class CardKnowledgeAdmin(admin.ModelAdmin):
    list_display = ['player', 'target_player', 'card', 'knowledge_type', 'confidence', 'is_shared']
    list_filter = ['knowledge_type', 'is_shared', 'confidence', 'updated_at']
    search_fields = ['player__name', 'target_player__name', 'card__name']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('player', 'target_player', 'card')


@admin.register(CardSharing)
class CardSharingAdmin(admin.ModelAdmin):
    list_display = ['from_player', 'to_player', 'card', 'sharing_type', 'is_public', 'created_at']
    list_filter = ['sharing_type', 'is_public', 'created_at']
    search_fields = ['from_player__name', 'to_player__name', 'card__name', 'message']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('from_player', 'to_player', 'card')


@admin.register(GameLog)
class GameLogAdmin(admin.ModelAdmin):
    list_display = ['session', 'player', 'action_type', 'description', 'created_at']
    list_filter = ['action_type', 'created_at']
    search_fields = ['session__name', 'player__name', 'description']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session', 'player')
    
    def has_add_permission(self, request):
        return False  # I log si creano automaticamente
    
    def has_change_permission(self, request, obj=None):
        return False  # I log non si modificano


# Configurazione admin personalizzata
admin.site.site_header = 'Cluedo Tracker Admin'
admin.site.site_title = 'Cluedo Tracker'
admin.site.index_title = 'Gestione Cluedo Tracker'