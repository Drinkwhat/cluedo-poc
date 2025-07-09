from django.core.management.base import BaseCommand
from django.core.management import call_command
import os


class Command(BaseCommand):
    help = 'Setup completo dell\'applicazione Cluedo Tracker'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-migrate',
            action='store_true',
            help='Salta le migrazioni del database',
        )
        parser.add_argument(
            '--skip-cards',
            action='store_true',
            help='Salta l\'inizializzazione delle carte',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🎯 Inizializzazione Cluedo Tracker...')
        )

        # Crea le migrazioni se non esistono
        if not options['skip_migrate']:
            self.stdout.write('📦 Creazione migrazioni...')
            call_command('makemigrations', verbosity=0)
            
            self.stdout.write('🗄️ Applicazione migrazioni...')
            call_command('migrate', verbosity=0)

        # Inizializza le carte
        if not options['skip_cards']:
            self.stdout.write('🃏 Inizializzazione carte Cluedo...')
            call_command('init_cluedo_cards', verbosity=0)

        # Crea superuser se non esiste
        self.stdout.write('👤 Controllo superuser...')
        try:
            from django.contrib.auth.models import User
            if not User.objects.filter(is_superuser=True).exists():
                self.stdout.write('Creazione superuser admin/admin...')
                User.objects.create_superuser('admin', 'admin@example.com', 'admin')
                self.stdout.write(
                    self.style.WARNING('⚠️ Superuser creato: admin/admin (cambia la password!)')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Errore nella creazione del superuser: {e}')
            )

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS('✅ Setup completato!')
        )
        self.stdout.write('')
        self.stdout.write('🚀 Per avviare il server in rete locale:')
        self.stdout.write('   python manage.py runserver 0.0.0.0:8000')
        self.stdout.write('')
        self.stdout.write('🌐 Accesso:')
        self.stdout.write('   - Host: http://localhost:8000/host/')
        self.stdout.write('   - Mobile: http://[IP_LOCALE]:8000/join/')
        self.stdout.write('   - API Docs: http://[IP_LOCALE]:8000/api/docs/')
        self.stdout.write('   - Admin: http://localhost:8000/admin/ (admin/admin)')
        self.stdout.write('')
