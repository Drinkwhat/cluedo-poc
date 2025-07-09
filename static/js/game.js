/**
 * Cluedo Game JavaScript - Django version
 * Main game functionality and WebSocket communication
 */

class CluedoGameApp {
    constructor() {
        this.config = window.GAME_CONFIG || {};
        this.websocket = null;
        this.gameData = null;
        this.currentUser = this.config.currentUser;
        this.sessionCode = this.config.sessionCode;
        this.connectionStatus = 'disconnected';
        
        this.init();
    }
    
    async init() {
        console.log('Initializing Cluedo Game App');
        
        // Load game data
        await this.loadGameData();
        
        // Initialize UI
        this.initializeUI();
        
        // Check for auto-create session
        if (this.config.autoCreateSession) {
            console.log('Auto-creating session...');
            setTimeout(() => {
                this.showTab('share');
                this.createSession();
            }, 1000);
        }
        
        // Connect WebSocket
        this.connectWebSocket();
        
        // Set up periodic heartbeat
        this.startHeartbeat();
        
        console.log('Game app initialized');
    }
    
    async loadGameData() {
        try {
            const response = await fetch(`${this.config.apiBase}gamedata/`);
            this.gameData = await response.json();
            console.log('Game data loaded:', this.gameData);
        } catch (error) {
            console.error('Error loading game data:', error);
            this.gameData = this.getDefaultGameData();
        }
    }
    
    getDefaultGameData() {
        return {
            characters: [
                'Miss Scarlett', 'Colonel Mustard', 'Mrs White', 
                'Rev Green', 'Mrs Peacock', 'Professor Plum'
            ],
            weapons: [
                'Candlestick', 'Knife', 'Lead Pipe', 
                'Revolver', 'Rope', 'Wrench'
            ],
            rooms: [
                'Kitchen', 'Ballroom', 'Conservatory', 'Dining Room',
                'Billiard Room', 'Library', 'Lounge', 'Hall', 'Study'
            ]
        };
    }
    
    initializeUI() {
        this.renderCards();
        this.loadPersonalNotes();
        this.setupEventListeners();
        this.updateConnectionStatus();
    }
    
    renderCards() {
        ['characters', 'weapons', 'rooms'].forEach(category => {
            const container = document.getElementById(category);
            if (!container) return;
            
            const cards = this.gameData[category] || [];
            container.innerHTML = cards.map(card => `
                <div class="card" data-card="${card}" data-category="${category.slice(0, -1)}">
                    <span class="card-name">${card}</span>
                    <div class="card-status">
                        <button class="status-btn mine" onclick="setCardStatus('${card}', 'mine')" title="Ho questa carta">
                            <i class="fas fa-check"></i>
                        </button>
                        <button class="status-btn shared" onclick="setCardStatus('${card}', 'shared')" title="Qualcuno ha mostrato questa carta">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="status-btn excluded" onclick="setCardStatus('${card}', 'excluded')" title="Nessuno ha questa carta">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            `).join('');
        });
        
        // Load saved card states
        this.loadCardStates();
    }
    
    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tabName = e.target.textContent.trim().toLowerCase();
                this.showTab(this.getTabId(tabName));
            });
        });
        
        // Share form
        const shareCardType = document.getElementById('shareCardType');
        if (shareCardType) {
            shareCardType.addEventListener('change', this.updateShareCardOptions.bind(this));
        }
    }
    
    getTabId(tabName) {
        const tabMap = {
            'carte': 'cards',
            'note': 'notes', 
            'condividi': 'share',
            'giocatori': 'players'
        };
        return tabMap[tabName] || 'cards';
    }
    
    showTab(tabName) {
        // Hide all tabs
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });
        
        // Remove active from all tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        // Show selected tab
        const tab = document.getElementById(`${tabName}-tab`);
        if (tab) {
            tab.classList.add('active');
        }
        
        // Activate corresponding button
        const btn = Array.from(document.querySelectorAll('.tab-btn')).find(b => 
            this.getTabId(b.textContent.trim().toLowerCase()) === tabName
        );
        if (btn) {
            btn.classList.add('active');
        }
    }
    
    connectWebSocket() {
        if (!this.config.websocketUrl) {
            console.warn('WebSocket URL not configured');
            return;
        }
        
        const wsUrl = `${this.config.websocketUrl}${this.sessionCode}/`;
        console.log('Connecting to WebSocket:', wsUrl);
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            console.log('WebSocket connected');
            this.connectionStatus = 'connected';
            this.updateConnectionStatus();
        };
        
        this.websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        this.websocket.onclose = () => {
            console.log('WebSocket disconnected');
            this.connectionStatus = 'disconnected';
            this.updateConnectionStatus();
            
            // Attempt to reconnect after delay
            setTimeout(() => this.connectWebSocket(), 5000);
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.connectionStatus = 'error';
            this.updateConnectionStatus();
        };
    }
    
    handleWebSocketMessage(data) {
        console.log('WebSocket message:', data);
        
        switch (data.type) {
            case 'session_data':
                this.updateSessionData(data.data);
                break;
            case 'card_share':
                this.handleCardShare(data.data);
                break;
            case 'user_update':
                this.updateUsersList(data.data);
                break;
            case 'heartbeat_response':
                console.log('Heartbeat acknowledged');
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }
    
    updateConnectionStatus() {
        const statusEl = document.getElementById('connectionStatus');
        if (!statusEl) return;
        
        statusEl.className = `connection-status ${this.connectionStatus}`;
        
        const iconMap = {
            'connected': 'fas fa-wifi',
            'disconnected': 'fas fa-wifi-slash',
            'error': 'fas fa-exclamation-triangle'
        };
        
        statusEl.innerHTML = `<i class="${iconMap[this.connectionStatus]}"></i>`;
    }
    
    startHeartbeat() {
        setInterval(() => {
            if (this.websocket && this.websocket.readyState === WebSocket.OPEN && this.currentUser) {
                this.websocket.send(JSON.stringify({
                    type: 'heartbeat',
                    user_id: this.currentUser.id,
                    timestamp: Date.now()
                }));
            }
        }, 30000); // Every 30 seconds
    }
    
    setCardStatus(cardName, status) {
        const card = document.querySelector(`[data-card="${cardName}"]`);
        if (!card) return;
        
        // Remove all status classes
        card.classList.remove('mine', 'shared', 'excluded');
        
        // Add new status class
        if (status !== 'none') {
            card.classList.add(status);
        }
        
        // Save to localStorage
        this.saveCardState(cardName, status);
        
        console.log(`Card ${cardName} set to ${status}`);
    }
    
    saveCardState(cardName, status) {
        const key = `cluedo_cards_${this.sessionCode}`;
        let cardStates = JSON.parse(localStorage.getItem(key)) || {};
        
        if (status === 'none') {
            delete cardStates[cardName];
        } else {
            cardStates[cardName] = status;
        }
        
        localStorage.setItem(key, JSON.stringify(cardStates));
    }
    
    loadCardStates() {
        const key = `cluedo_cards_${this.sessionCode}`;
        const cardStates = JSON.parse(localStorage.getItem(key)) || {};
        
        Object.entries(cardStates).forEach(([cardName, status]) => {
            const card = document.querySelector(`[data-card="${cardName}"]`);
            if (card) {
                card.classList.add(status);
            }
        });
    }
    
    updateShareCardOptions() {
        const cardType = document.getElementById('shareCardType').value;
        const cardSelect = document.getElementById('shareCard');
        
        if (!cardType || !cardSelect) return;
        
        const cards = this.gameData[cardType + 's'] || [];
        cardSelect.innerHTML = '<option value="">Seleziona carta...</option>' +
            cards.map(card => `<option value="${card}">${card}</option>`).join('');
    }
    
    async shareCard() {
        const playerId = document.getElementById('sharePlayer').value;
        const cardType = document.getElementById('shareCardType').value;
        const cardName = document.getElementById('shareCard').value;
        
        if (!playerId || !cardType || !cardName) {
            alert('Compila tutti i campi per condividere una carta');
            return;
        }
        
        const shareData = {
            from_user_id: this.currentUser.id,
            to_user_id: playerId,
            card_type: cardType,
            card_name: cardName
        };
        
        // Send via WebSocket
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({
                type: 'card_share',
                ...shareData
            }));
        }
        
        // Reset form
        document.getElementById('sharePlayer').value = '';
        document.getElementById('shareCardType').value = '';
        document.getElementById('shareCard').value = '';
        
        console.log('Card shared:', shareData);
    }
    
    saveNotes() {
        const notes = document.getElementById('personalNotes').value;
        const key = `cluedo_notes_${this.sessionCode}`;
        localStorage.setItem(key, notes);
        
        // Show feedback
        const btn = event.target;
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-check"></i> Salvato!';
        setTimeout(() => {
            btn.innerHTML = originalText;
        }, 2000);
    }
    
    loadPersonalNotes() {
        const key = `cluedo_notes_${this.sessionCode}`;
        const notes = localStorage.getItem(key);
        const notesEl = document.getElementById('personalNotes');
        
        if (notesEl && notes) {
            notesEl.value = notes;
        }
    }
    
    async endSession() {
        if (!confirm('Sei sicuro di voler terminare questa sessione?')) {
            return;
        }
        
        try {
            const response = await fetch(`${this.config.apiBase}session/${this.sessionCode}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.config.csrfToken
                }
            });
            
            if (response.ok) {
                alert('Sessione terminata');
                window.location.href = '/';
            } else {
                alert('Errore nel terminare la sessione');
            }
        } catch (error) {
            console.error('Error ending session:', error);
            alert('Errore nel terminare la sessione');
        }
    }
    
    async createSession() {
        try {
            const playerName = localStorage.getItem('playerName') || 'Giocatore';
            const response = await fetch(`${this.config.apiBase}session/create/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.config.csrfToken
                },
                body: JSON.stringify({
                    name: playerName
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.sessionCode = data.session_code;
                console.log('Session created:', data);
                this.updateSessionDisplay(data);
                return data;
            } else {
                console.error('Error creating session:', response.statusText);
                return null;
            }
        } catch (error) {
            console.error('Error creating session:', error);
            return null;
        }
    }
    
    updateSessionDisplay(sessionData) {
        const sessionCodeEl = document.getElementById('sessionCode');
        if (sessionCodeEl) {
            sessionCodeEl.textContent = sessionData.session_code;
        }
        
        // Show QR code button if available
        const qrBtn = document.getElementById('qrBtn');
        if (qrBtn) {
            qrBtn.style.display = 'inline-block';
        }
    }
    
    joinSession(sessionCode) {
        // Join an existing session
        this.sessionCode = sessionCode;
        this.connectWebSocket();
    }
    
    finishSetup() {
        // Finalize setup, e.g., start the game or update UI
        console.log('Setup finished');
        
        // For now, just show the cards tab
        this.showTab('cards');
    }
}

// Global functions for template access
window.showTab = function(tabName) {
    if (window.gameApp) {
        window.gameApp.showTab(tabName);
    }
};

window.setCardStatus = function(cardName, status) {
    if (window.gameApp) {
        window.gameApp.setCardStatus(cardName, status);
    }
};

window.shareCard = function() {
    if (window.gameApp) {
        window.gameApp.shareCard();
    }
};

window.saveNotes = function() {
    if (window.gameApp) {
        window.gameApp.saveNotes();
    }
};

window.endSession = function() {
    if (window.gameApp) {
        window.gameApp.endSession();
    }
};

window.regenerateSessionCode = function() {
    if (window.gameApp) {
        window.gameApp.createSession();
    }
};

window.copySessionCode = function() {
    const sessionCode = document.getElementById('sessionCode').textContent;
    if (sessionCode && sessionCode !== 'Generando...') {
        navigator.clipboard.writeText(sessionCode).then(() => {
            alert('Codice sessione copiato!');
        }).catch(err => {
            console.error('Could not copy text: ', err);
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = sessionCode;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            alert('Codice sessione copiato!');
        });
    }
};

// Setup Wizard Functions
window.hostNewSession = function() {
    // Redirect to the auto-session creation page
    window.location.href = '/create/';
};

window.joinSessionSetup = function() {
    const sessionCode = document.getElementById('setupSessionCode').value.trim().toUpperCase();
    if (!sessionCode) {
        alert('Inserisci un codice sessione valido');
        return;
    }
    
    if (window.gameApp) {
        window.gameApp.joinSession(sessionCode);
        // Move to next step
        nextStep();
    }
};

window.startOfflineGame = function() {
    // Skip to player name step for offline mode
    nextStep();
};

window.nextStep = function() {
    const currentStep = document.querySelector('.setup-step.active');
    const nextStep = currentStep.nextElementSibling;
    
    if (nextStep) {
        currentStep.classList.remove('active');
        nextStep.classList.add('active');
    }
};

window.previousStep = function() {
    const currentStep = document.querySelector('.setup-step.active');
    const prevStep = currentStep.previousElementSibling;
    
    if (prevStep) {
        currentStep.classList.remove('active');
        prevStep.classList.add('active');
    }
};

window.confirmPlayerName = function() {
    const playerName = document.getElementById('setupPlayerName').value.trim();
    if (!playerName) {
        alert('Inserisci il tuo nome');
        return;
    }
    
    // Save player name
    localStorage.setItem('playerName', playerName);
    document.getElementById('playerName').value = playerName;
    
    if (window.gameApp) {
        window.gameApp.currentUser = playerName;
    }
    
    // Move to next step
    nextStep();
};

window.finishSetup = function() {
    // Hide setup wizard
    document.getElementById('setupWizard').style.display = 'none';
    
    // Initialize game with selected cards
    if (window.gameApp) {
        window.gameApp.finishSetup();
    }
};

// Additional utility functions
window.addPlayer = function() {
    if (window.gameApp) {
        window.gameApp.addPlayer();
    }
};

window.joinExistingSession = function() {
    const sessionCode = document.getElementById('joinSessionCode').value.trim().toUpperCase();
    if (!sessionCode) {
        alert('Inserisci un codice sessione valido');
        return;
    }
    
    if (window.gameApp) {
        window.gameApp.joinSession(sessionCode);
    }
};

window.refreshConnectedUsers = function() {
    if (window.gameApp) {
        window.gameApp.refreshConnectedUsers();
    }
};

window.shareWithPlayer = function() {
    if (window.gameApp) {
        window.gameApp.shareWithPlayer();
    }
};

window.checkForUpdates = function() {
    if (window.gameApp) {
        window.gameApp.checkForUpdates();
    }
};

window.exportData = function() {
    if (window.gameApp) {
        window.gameApp.exportData();
    }
};

window.importData = function() {
    if (window.gameApp) {
        window.gameApp.importData();
    }
};

window.resetAll = function() {
    if (confirm('Sei sicuro di voler cancellare tutti i dati? Questa azione non può essere annullata.')) {
        if (window.gameApp) {
            window.gameApp.resetAll();
        }
    }
};

window.openSessionManager = function() {
    if (window.gameApp && window.gameApp.sessionCode) {
        // Open session management page
        window.open(`/session/${window.gameApp.sessionCode}`, '_blank');
    }
};

window.closeModal = function() {
    document.getElementById('cardModal').style.display = 'none';
};

window.confirmShownCard = function() {
    if (window.gameApp) {
        window.gameApp.confirmShownCard();
    }
};

// Debug functions
let debugTapCount = 0;
window.handleDebugTouch = function(event) {
    debugTapCount++;
    if (debugTapCount >= 3) {
        debugTapCount = 0;
        if (window.gameApp) {
            window.gameApp.toggleDebugMode();
        }
    }
    setTimeout(() => {
        debugTapCount = 0;
    }, 1000);
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.gameApp = new CluedoGameApp();
});
