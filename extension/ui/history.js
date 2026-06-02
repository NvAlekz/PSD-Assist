/**
 * Pokemon Showdown Assistant - Historial Visual
 * Panel para visualizar el historial de la batalla en tiempo real
 */

class BattleHistory {
  constructor(container) {
    this.container = container;
    this.events = [];
    this.maxEvents = 50;
    this.init();
  }

  init() {
    this.render();
    this.startPolling();
  }

  startPolling() {
    setInterval(() => this.update(), 2000);
  }

  update() {
    chrome.runtime.sendMessage({ type: 'GET_BATTLE_HISTORY' }, (history) => {
      if (history && history.length > this.events.length) {
        this.events = history.slice(-this.maxEvents);
        this.render();
      }
    });
  }

  render() {
    if (!this.container) return;
    
    this.container.innerHTML = `
      <div class="psd-history">
        <h4>📜 Historial de Batalla</h4>
        <div class="psd-history-list">
          ${this.events.map((event, i) => this.renderEvent(event, i)).join('')}
        </div>
      </div>
    `;
    
    this.container.scrollTop = this.container.scrollHeight;
  }

  renderEvent(event, index) {
    const time = new Date(event.timestamp).toLocaleTimeString();
    const icon = this.getEventIcon(event.type);
    
    return `
      <div class="psd-history-event" data-index="${index}">
        <span class="psd-history-time">${time}</span>
        <span class="psd-history-icon">${icon}</span>
        <span class="psd-history-text">${this.formatEvent(event)}</span>
      </div>
    `;
  }

  getEventIcon(type) {
    const icons = {
      'switch': '🔄',
      'move': '⚔️',
      'damage': '💥',
      'status': '💫',
      'faint': '💀',
      'heal': '💚',
      'hazard': '⚡',
      'weather': '🌦️',
      'turn': '📍'
    };
    return icons[type] || '📋';
  }

  formatEvent(event) {
    switch (event.type) {
      case 'switch':
        return `${event.pokemon} entró a combate`;
      case 'move':
        return `${event.pokemon} usó ${event.move}`;
      case 'damage':
        return `${event.target} recibió ${event.damage} de daño`;
      case 'status':
        return `${event.target} está ${event.status}`;
      case 'faint':
        return `${event.pokemon} se debilitó`;
      case 'turn':
        return `--- Turno ${event.turn} ---`;
      default:
        return event.description || 'Acción desconocida';
    }
  }

  addEvent(event) {
    this.events.push({
      ...event,
      timestamp: Date.now()
    });
    
    if (this.events.length > this.maxEvents) {
      this.events.shift();
    }
    
    this.render();
  }
}

// CSS para el historial
const historyStyles = `
.psd-history {
  background: rgba(20, 20, 30, 0.95);
  border: 1px solid #3498db;
  border-radius: 8px;
  padding: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.psd-history h4 {
  margin: 0 0 10px 0;
  color: #3498db;
  font-size: 14px;
}

.psd-history-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.psd-history-event {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  font-size: 12px;
}

.psd-history-time {
  color: #7f8c8d;
  font-size: 10px;
  min-width: 60px;
}

.psd-history-icon {
  font-size: 14px;
}

.psd-history-text {
  color: #ecf0f1;
  flex: 1;
}
`;

// Inyectar estilos
const styleElement = document.createElement('style');
styleElement.textContent = historyStyles;
document.head.appendChild(styleElement);

window.BattleHistory = BattleHistory;