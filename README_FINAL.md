# 🎯 Cluedo Tracker - Gestione Carte in Rete Locale

Un'applicazione Django per gestire le carte di Cluedo tramite rete locale, permettendo ai giocatori di condividere e tracciare le informazioni sulle carte in tempo reale.

![Django](https://img.shields.io/badge/Django-5.0-green)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🚀 Caratteristiche Principali

### 🌐 Rete Locale
- **Accesso Multi-Dispositivo**: Computer (host) + telefoni (giocatori)
- **Auto-Discovery IP**: Rileva automaticamente l'IP locale
- **QR Code**: Accesso rapido per i dispositivi mobili
- **WebSocket**: Aggiornamenti in tempo reale

### 🃏 Gestione Carte
- **21 Carte Standard**: Personaggi, armi e stanze del Cluedo
- **Tracciamento Individuale**: Ogni giocatore gestisce le proprie carte
- **Condivisione Controllata**: Opzioni per condividere informazioni
- **Sistema di Deduzione**: Traccia le conoscenze su altre carte

### 🎮 Interfacce Separate
- **Host Dashboard**: Crea e gestisce sessioni, monitora progresso
- **Player Interface**: Mobile-friendly per gestire carte e note
- **API RESTful**: Django Ninja con documentazione automatica

### 📊 Funzionalità Avanzate
- **Note Personali**: Ogni giocatore può prendere note private
- **Log Attività**: Traccia tutte le azioni della partita
- **Statistiche**: Monitoraggio in tempo reale del progresso
- **PWA Ready**: Installabile come app mobile

## 🛠️ Installazione Rapida

```bash
# 1. Clona il repository
git clone <repository-url>
cd cluedo2

# 2. Setup completo automatico
make quickstart

# 3. Avvia il server per rete locale
make run-local
```

## 📱 Come Giocare

### 1. Setup Host (Computer)
```bash
# Avvia il server
python manage.py runserver 0.0.0.0:8000

# Apri il browser
http://localhost:8000/host/
```

### 2. Crea Sessione
- Vai su `/host/`
- Clicca "Crea Nuova Sessione"
- Configura nome e opzioni
- Ottieni codice sessione e QR code

### 3. Giocatori si Uniscono (Telefoni)
- Scansiona QR code O vai su `http://[IP_LOCALE]:8000/join/`
- Inserisci codice sessione
- Scegli nome e personaggio
- Inizia a giocare!

### 4. Gestisci Carte
- **Aggiungi carte**: Seleziona le carte che possiedi
- **Condividi info**: Rivela informazioni ad altri giocatori
- **Prendi note**: Annota deduzioni e strategie
- **Monitora progresso**: Vedi aggiornamenti in tempo reale

## 🌐 Architettura Tecnica

```
├── Frontend (Templates + JavaScript)
│   ├── Host Dashboard (Computer)
│   ├── Player Interface (Mobile)
│   └── Real-time WebSocket
│
├── Backend (Django + Ninja API)
│   ├── Class-Based Views
│   ├── RESTful API Endpoints
│   ├── WebSocket Consumers
│   └── Background Tasks
│
├── Database (SQLite/PostgreSQL)
│   ├── Sessions & Players
│   ├── Cards & PlayerCards
│   ├── Knowledge & Sharing
│   └── Activity Logs
│
└── Network Layer
    ├── Local IP Discovery
    ├── QR Code Generation
    └── CORS Configuration
```

## 🔧 Configurazione Avanzata

### Environment Variables
```bash
# Copia e modifica il file di configurazione
cp .env.example .env

# Modifica le impostazioni
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=*
```

### Database
```bash
# SQLite (default)
python manage.py migrate

# PostgreSQL (opzionale)
# Configura DATABASE_URL nel .env
```

### Comando Personalizzati
```bash
# Setup completo
python manage.py setup_cluedo

# Inizializza solo le carte
python manage.py init_cluedo_cards

# Reset completo database
make reset-db
```

## 📚 API Documentation

L'API è completamente documentata con Django Ninja:

- **Docs URL**: `http://localhost:8000/api/docs/`
- **OpenAPI Schema**: `http://localhost:8000/api/openapi.json`

### Endpoints Principali

```python
# Sessioni
GET    /api/sessions/              # Lista sessioni
POST   /api/sessions/              # Crea sessione
GET    /api/sessions/{code}/       # Dettagli sessione

# Giocatori
GET    /api/sessions/{code}/players/     # Lista giocatori
POST   /api/sessions/{code}/players/     # Unisciti sessione

# Carte
GET    /api/cards/                       # Lista carte
PUT    /api/sessions/{code}/players/{id}/cards/  # Aggiorna carte

# Condivisione
POST   /api/sessions/{code}/share-card/  # Condividi carta
GET    /api/sessions/{code}/shared-cards/ # Carte condivise

# Utilità
GET    /api/connection-info/             # Info connessione
GET    /api/health/                      # Health check
```

## 🎯 Casi d'Uso

### 🏠 Famiglia a Casa
- Host sul computer del salotto
- Ogni membro famiglia con il proprio telefono
- Condivisione permessa per aiutare i più piccoli

### 🎲 Gruppo di Amici
- Host su laptop
- Tutti con i propri dispositivi
- Modalità competitiva con condivisione limitata

### 🏫 Ambiente Educativo
- Insegnante come host
- Studenti con tablet/telefoni
- Tracciamento completo per scopi didattici

## 🔍 Troubleshooting

### Problemi Comuni

**QR Code non funziona**
```bash
# Verifica che i dispositivi siano sulla stessa rete
# Controlla il firewall del computer host
# Riavvia il server con: make run-local
```

**Giocatori non si connettono**
```bash
# Verifica l'IP locale
python -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('8.8.8.8', 80)); print(s.getsockname()[0]); s.close()"

# Testa la connettività
curl http://[IP_LOCALE]:8000/api/health/
```

**Database corrotto**
```bash
# Reset completo
make reset-db

# O manualmente
rm db.sqlite3
python manage.py migrate
python manage.py init_cluedo_cards
```

## 🚧 Sviluppo

### Setup Ambiente di Sviluppo
```bash
# Installa dipendenze dev
pip install -r requirements.txt

# Avvia in modalità debug
DEBUG=True python manage.py runserver 0.0.0.0:8000

# Test
python manage.py test
```

### Struttura Codice
```
app/
├── models.py          # Modelli database
├── views.py           # Class-based views
├── api.py             # Django Ninja API
├── consumers.py       # WebSocket consumers
├── routing.py         # WebSocket routing
├── admin.py           # Django admin
├── urls.py            # URL patterns
└── management/
    └── commands/      # Comandi personalizzati
```

## 📄 License

MIT License - vedi [LICENSE](LICENSE) per dettagli.

## 🤝 Contribuire

1. Fork il progetto
2. Crea un branch per la feature (`git checkout -b feature/AmazingFeature`)
3. Commit le modifiche (`git commit -m 'Add some AmazingFeature'`)
4. Push sul branch (`git push origin feature/AmazingFeature`)
5. Apri una Pull Request

## 📞 Supporto

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Documentation**: [Wiki](https://github.com/your-repo/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)

---

**Buon divertimento con il vostro Cluedo digitale! 🕵️‍♂️🔍**
