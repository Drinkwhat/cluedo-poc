# Makefile per Cluedo Tracker - Gestione Carte in Rete Locale

.PHONY: help install setup run run-local clean migrate test

# Configurazione
PYTHON = python
MANAGE = $(PYTHON) manage.py
PORT = 8000

help: ## Mostra questo messaggio di aiuto
	@echo "🎯 Cluedo Tracker - Comandi Disponibili:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""

install: ## Installa le dipendenze
	@echo "📦 Installazione dipendenze..."
	pip install -r requirements.txt

setup: ## Setup completo dell'applicazione
	@echo "🚀 Setup completo Cluedo Tracker..."
	$(MANAGE) setup_cluedo

migrate: ## Esegui migrazioni database
	@echo "🗄️ Esecuzione migrazioni..."
	$(MANAGE) makemigrations
	$(MANAGE) migrate

init-cards: ## Inizializza le carte del Cluedo
	@echo "🃏 Inizializzazione carte..."
	$(MANAGE) init_cluedo_cards

run: ## Avvia il server (solo localhost)
	@echo "🖥️ Avvio server localhost..."
	$(MANAGE) runserver $(PORT)

run-local: ## Avvia il server per rete locale
	@echo "🌐 Avvio server per rete locale..."
	@echo "I dispositivi sulla stessa Wi-Fi potranno connettersi"
	$(MANAGE) runserver 0.0.0.0:$(PORT)

# Quick start per nuovi utenti
quickstart: ## Setup rapido per iniziare subito
	@echo "🎯 Quick Start Cluedo Tracker"
	@echo "=============================="
	$(MAKE) install
	$(MAKE) setup
	@echo ""
	@echo "✅ Setup completato!"
	@echo ""
	@echo "🚀 Per iniziare:"
	@echo "   make run-local"
	@echo ""
	@echo "🌐 Poi apri:"
	@echo "   http://localhost:$(PORT)/host/ (sul computer)"
	@echo ""
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build dell'immagine Docker
	docker-compose build

up: ## Avvia l'applicazione
	docker-compose up -d

down: ## Ferma l'applicazione
	docker-compose down

logs: ## Mostra i logs
	docker-compose logs -f

shell: ## Apri shell Django
	docker-compose exec web python manage.py shell

migrate: ## Esegui migrazioni
	docker-compose exec web python manage.py migrate

makemigrations: ## Crea nuove migrazioni
	docker-compose exec web python manage.py makemigrations

test: ## Esegui i test
	docker-compose exec web python manage.py test

dev: ## Avvia in modalità sviluppo con live reload
	docker-compose up

setup: build up migrate ## Setup completo del progetto
	@echo "🎯 Progetto Cluedo Card Tracker avviato!"
	@echo "📱 Accedi a: http://localhost:8000"

clean: ## Pulisci containers e volumi
	docker-compose down -v
	docker system prune -f

# Gestione processi e porte
kill-server: ## Termina il server Django se in esecuzione
	@echo "🔄 Terminazione server esistente..."
	@-lsof -ti:$(PORT) | xargs kill -9 2>/dev/null || echo "Nessun processo da terminare"

check-port: ## Controlla cosa usa la porta
	@echo "🔍 Controllo porta $(PORT):"
	@lsof -i:$(PORT) || echo "Porta $(PORT) libera"

restart: kill-server run-local ## Termina e riavvia il server

status: ## Mostra lo stato del server
	@echo "📊 Status del sistema:"
	@ps aux | grep "manage.py runserver" | grep -v grep || echo "Server non in esecuzione"
	@echo ""
	@make check-port