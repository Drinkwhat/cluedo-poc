from django.core.management.base import BaseCommand
from cluedo_game.models import initialize_cluedo_cards, Card


class Command(BaseCommand):
    help = 'Inizializza le carte standard del Cluedo nel database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forza la creazione anche se le carte esistono già',
        )

    def handle(self, *args, **options):
        if not options['force'] and Card.objects.exists():
            self.stdout.write(
                self.style.WARNING('Le carte esistono già. Usa --force per forzare la ricreazione.')
            )
            return

        if options['force']:
            Card.objects.all().delete()
            self.stdout.write('Carte esistenti eliminate.')

        before_count = Card.objects.count()
        initialize_cluedo_cards()
        after_count = Card.objects.count()

        self.stdout.write(
            self.style.SUCCESS(
                f'Carte inizializzate con successo! '
                f'Carte create: {after_count - before_count}, '
                f'Totale carte: {after_count}'
            )
        )

        # Mostra riepilogo carte per tipo
        for card_type, type_name in Card.CARD_TYPES:
            count = Card.objects.filter(card_type=card_type).count()
            self.stdout.write(f'  - {type_name}: {count} carte')
