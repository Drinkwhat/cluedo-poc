# 🌐 Guida Completa: Cluedo Tracker con IP Locale

## 📋 Panoramica

Il Cluedo Tracker ora supporta l'**accesso da dispositivi multipli** sulla stessa rete Wi-Fi:
- **Computer (Host)**: Crea e gestisce la sessione
- **Telefoni (Giocatori)**: Si uniscono tramite QR code o codice sessione

## 🚀 Come Iniziare

### 1. Avvia il Server per la Rete Locale

Per permettere l'accesso da altri dispositivi, avvia Django con:

```bash
# Permette connessioni da tutti i dispositivi sulla rete
python manage.py runserver 0.0.0.0:8000
```

### 2. Computer Host - Crea Sessione

1. **Apri il browser** sul computer e vai su: `http://localhost:8000/host/`
2. **Crea una nuova sessione** inserendo un nome
3. **Condividi** il QR code o il codice sessione

### 3. Telefono - Unisciti alla Sessione

**Opzione 1: QR Code** 📷
- Scansiona il QR code mostrato sul computer
- Verrai reindirizzato automaticamente alla pagina mobile

**Opzione 2: Codice Manuale** ⌨️
- Vai su `http://[IP_DEL_COMPUTER]:8000/mobile/join/`
- Inserisci il codice sessione mostrato sul computer

## 🔧 Funzionalità Implementate

### ✅ Rilevamento IP Automatico
- Il sistema rileva automaticamente l'IP locale della macchina
- I QR code contengono l'IP corretto invece di localhost
- L'interfaccia host mostra l'IP e l'URL mobile in tempo reale

### ✅ Interface Separati
- **Computer Host**: `/host/` - Creazione, gestione, monitoraggio
- **Mobile Players**: `/mobile/` - Unione semplificata, gestione carte

### ✅ API Moderne
- **Router-based API**: Endpoints RESTful con ViewSets
- **Legacy API**: Compatibilità con versioni precedenti
- **Real-time Updates**: Informazioni di connessione dinamiche

## 📱 Come Funziona il Flusso

```
1. Computer Host
   └── Crea sessione → Ottiene QR + Codice

2. Telefono Giocatore  
   └── Scansiona QR → Inserisce nome/personaggio → Aggiunge carte

3. Computer Host
   └── Vede giocatori in tempo reale → Monitora progresso

4. Telefono Giocatore
   └── Gestisce le proprie carte → Aggiorna conoscenze
```

## 🌐 Indirizzi e URL

### Computer Host
- **Homepage Host**: `http://localhost:8000/host/`
- **Gestione Sessione**: `http://localhost:8000/host/session/{ID}/`

### Mobile Players
- **Join Page**: `http://[IP_LOCALE]:8000/mobile/join/`
- **Player Interface**: `http://[IP_LOCALE]:8000/mobile/session/{ID}/`

### API Endpoints
- **Connection Info**: `/api/connection-info/` - Ottiene IP locale e URL
- **Sessions**: `/api/sessions/` - Gestione sessioni moderne
- **QR Code**: `/session/{ID}/qr/` - Genera QR con IP locale

## 🔍 Test e Debug

### Test Funzionalità
```bash
# Test completo API e IP
python test_ip_functionality.py

# Test router API
python test_router_api.py

# Test API legacy
python test_api.py
```

### Debug Connessione
1. **Verifica IP**: `curl http://localhost:8000/api/connection-info/`
2. **Test QR Code**: Controlla che il QR contenga l'IP locale
3. **Test Mobile**: Accedi da un altro dispositivo sulla stessa rete

## 💡 Consigli per l'Uso

### Per l'Host (Computer)
- Tieni aperta la pagina host per monitorare i giocatori
- Condividi il QR code o mostra il codice sessione
- Usa le statistiche per verificare che tutti abbiano le carte

### Per i Giocatori (Telefono)
- Scansiona il QR code per un accesso rapido
- Inserisci tutte le tue carte all'inizio
- Aggiorna le conoscenze durante il gioco

### Risoluzione Problemi
- **QR non funziona**: Verifica che entrambi i dispositivi siano sulla stessa Wi-Fi
- **Pagina non carica**: Controlla che il server sia avviato con `0.0.0.0:8000`
- **IP non corretto**: Riavvia il server, l'IP viene rilevato al startup

## 📊 Architettura Tecnica

```
Frontend (Templates)
├── host_session.html → Interface computer host
├── mobile_join.html → Pagina unione mobile  
└── mobile_player.html → Interface giocatore mobile

Backend (API)
├── api_router.py → ViewSets moderni DRF
├── api_viewsets.py → Serializers e logica API
├── api.py → API legacy per compatibilità
└── views.py → Views per interface web

Database
├── GameSession → Sessioni di gioco
├── Player → Giocatori e personaggi
├── Card → Carte dei giocatori
└── CardKnowledge → Matrice conoscenze
```

## 🎯 Prossimi Miglioramenti

- [ ] **WebSocket**: Updates in tempo reale per tutti i giocatori
- [ ] **PWA**: App mobile installabile 
- [ ] **Configurazione Rete**: Setup automatico firewall/rete
- [ ] **Multi-sessione**: Gestione multiple sessioni simultanee
- [ ] **Analytics**: Statistiche avanzate di gioco

---

## ✅ Stato Attuale

🟢 **Completato**:
- ✅ Rilevamento IP automatico
- ✅ QR code con IP locale
- ✅ Interface separati computer/mobile
- ✅ API moderne con ViewSets
- ✅ Compatibilità legacy
- ✅ Test completi

🟡 **In Produzione**:
- Sistema pronto per l'uso su rete locale
- Testato su macOS con Python 3.13
- Django 5.1 + DRF 3.15

**Per iniziare subito**: `python manage.py runserver 0.0.0.0:8000` e vai su `/host/`!
