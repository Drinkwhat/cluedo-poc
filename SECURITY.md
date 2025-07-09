# 🔒 Sicurezza - Cluedo Tracker

## ⚠️ **IMPORTANTE - PRIMA DI USARE IN PRODUZIONE**

### 1. **Cambia la SECRET_KEY**
```bash
# Genera una nuova SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 2. **Cambia le credenziali admin**
Le credenziali di default sono:
- Username: `admin`
- Password: `admin`
- Email: `admin@example.com`

**CAMBIA IMMEDIATAMENTE** dopo il setup:
```bash
python manage.py changepassword admin
```

### 3. **Configurazione per produzione**
- Imposta `DEBUG=False` in `.env`
- Configura `ALLOWED_HOSTS` correttamente
- Usa database più robusto (PostgreSQL)
- Configura HTTPS
- Configura email reali se necessario

### 4. **File sensibili non inclusi**
- `.env` - Configurazioni ambiente
- `db.sqlite3` - Database
- `media/` - File caricati
- `staticfiles/` - File statici generati

## 📁 **Struttura del Progetto**

```
cluedo2/
├── config/                  # Configurazione Django
│   ├── settings.py          # Configurazioni globali
│   ├── urls.py              # URL routing principale
│   └── wsgi.py/asgi.py      # Server interfaces
├── cluedo_game/             # App Django per il gioco
│   ├── models.py            # Modelli database
│   ├── views.py             # Logica di business
│   ├── api.py               # API endpoints
│   └── management/commands/ # Comandi personalizzati
├── templates/               # Template HTML
├── static/                  # File statici (CSS, JS)
└── requirements.txt         # Dipendenze Python
```

## 🚨 **Uso in Rete Locale**
Questo progetto è progettato per l'uso in rete locale. Per l'uso in produzione online, ulteriori misure di sicurezza sono necessarie.
