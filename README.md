# 🕵️ Cluedo Mobile Tracker

> **Versione 2.0 - Django Ninja API Edition**

Applicazione web mobile-first per tracciare le carte durante una partita a Cluedo, con API moderna e interfaccia PWA.

## 🚀 Caratteristiche Principali

- **🎮 Interfaccia Moderna**: PWA mobile-first con design responsivo
- **⚡ API Veloce**: Django Ninja con documentazione automatica
- **🔗 Sessioni Condivise**: Codici sessione a 8 caratteri per multiplayer
- **📱 Mobile Ready**: Installabile come app nativa
- **🎯 Real-time**: Gestione carte e conoscenze in tempo reale

## 🛠️ Stack Tecnologico

- **Backend**: Django 4.2 + Django Ninja
- **Frontend**: HTML5, CSS3, JavaScript ES6+
- **Database**: SQLite (locale)
- **API**: RESTful con Ninja + documentazione OpenAPI
- **PWA**: Service Worker + Manifest

## 📋 Requisiti

- Python 3.8+
- Django 4.2+
- Django Ninja

## 🚀 Installazione e Avvio

```bash
# Clona il repository
git clone <repo-url>
cd cluedo2

# Crea ambiente virtuale
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Installa dipendenze
pip install -r requirements.txt

# Migra database
python manage.py migrate

# Avvia server
python manage.py runserver
```

## 🔗 URL Principali

- **App Principale**: http://127.0.0.1:8000/
- **API Documentation**: http://127.0.0.1:8000/api/docs/
- **API Base**: http://127.0.0.1:8000/api/
- **Host Interface**: http://127.0.0.1:8000/host/

## 🎯 API Endpoints (Django Ninja)

### 🎮 Game Data
- `GET /api/gamedata` - Ottieni carte Cluedo

### 🎪 Sessions
- `POST /api/session/create` - Crea sessione
- `POST /api/session/join` - Unisciti a sessione
- `GET /api/sessions` - Lista sessioni attive
- `GET /api/session/{id}` - Dettagli sessione

### 🃏 Cards
- `POST /api/session/{id}/cards/add` - Aggiungi carta
- `DELETE /api/session/{id}/cards/{name}` - Rimuovi carta

### 🔧 Utility
- `GET /api/health` - Health check

## 🎮 Come Giocare

### 1. 🏠 Host (Computer)
1. Vai su http://127.0.0.1:8000/
2. Il sistema genererà automaticamente un codice sessione
3. Condividi il codice con gli altri giocatori

### 2. 📱 Mobile Players
1. Apri http://127.0.0.1:8000/ sul telefono
2. Inserisci il codice sessione ricevuto
3. Aggiungi il tuo nome
4. Seleziona le tue carte iniziali

### 3. 🎯 Durante il Gioco
- Traccia le carte mostrate dagli altri giocatori
- Prendi note personali
- Aggiorna le tue conoscenze
- Usa la deduzione per vincere!

## 📁 Struttura Progetto

```
cluedo2/
├── cards_app/
│   ├── ninja_api.py      # 🔥 API moderna Django Ninja
│   ├── models.py         # Modelli database
│   ├── views.py          # Views web + legacy API
│   └── urls.py           # Routing
├── templates/
│   ├── index.html        # 🎮 App principale moderna
│   └── ...
├── static/
│   ├── styles.css        # 🎨 CSS moderno
│   ├── js/game.js        # ⚡ Logic JavaScript
│   └── manifest.json     # 📱 PWA config
└── test_ninja_integration.py  # 🧪 Test completi
```

## 🧪 Testing

```bash
# Test completo dell'integrazione
python test_ninja_integration.py

# Test manuale API
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/gamedata
```

## 🔧 Sviluppo

### Debug Mode
Aggiungi `?debug=1` all'URL per modalità debug

### API Testing
Usa la documentazione interattiva su `/api/docs/` per testare gli endpoint

### Hot Reload
Il server Django ricarica automaticamente le modifiche

## 🏆 Funzionalità Avanzate

- **QR Codes**: Per condivisione rapida sessioni
- **PWA**: Installabile come app mobile
- **Offline Ready**: Funzionalità base offline
- **Auto-save**: Salvataggio automatico dello stato
- **Responsive**: Ottimizzato per tutti i dispositivi

## 📱 PWA Installation

Su mobile:
1. Apri l'app nel browser
2. Cerca "Aggiungi alla schermata Home"
3. L'app sarà installabile come nativa

## 🤝 Contribuzione

1. Fork del progetto
2. Crea feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit (`git commit -m 'Add some AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Apri Pull Request

## 📜 Licenza

Distribuito sotto licenza MIT. Vedi `LICENSE` per maggiori informazioni.

## 🎯 Roadmap

- [ ] WebSocket per aggiornamenti real-time
- [ ] Algoritmi di deduzione automatica
- [ ] Statistiche di gioco
- [ ] Tornei e classifiche
- [ ] Integrazione social

---

**Made with ❤️ for Cluedo enthusiasts**
