/**
 * Pokemon Showdown Assistant - Overlay Panel
 * Panel principal con recomendaciones y estado de batalla
 */

class OverlayPanel {
  constructor() {
    this.element = null;
    this.isVisible = false;
    this.history = new BattleHistoryComponent();
    this.init();
  }

  init() {
    this.createElement();
    this.injectStyles();
    this.setupMessageListeners();
  }

  createElement() {
    this.element = document.createElement('div');
    this.element.id = 'psd-overlay-panel';
    this.element.className = 'psd-overlay-panel';
    this.element.style.display = 'none';
    document.body.appendChild(this.element);
  }

  injectStyles() {
    const styles = document.createElement('style');
    styles.textContent = `
      .psd-overlay-panel {
        position: fixed;
        top: 20px;
        right: 20px;
        width: 320px;
        background: rgba(20, 20, 30, 0.98);
        border: 2px solid #3498db;
        border-radius: 12px;
        font-family: 'Segoe UI', Tahoma, sans-serif;
        color: #fff;
        z-index: 99999;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        overflow: hidden;
      }
      
      .psd-overlay-header {
        background: linear-gradient(135deg, #2c3e50, #3498db);
        padding: 12px 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      
      .psd-overlay-header h3 {
        margin: 0;
        font-size: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
      }
      
      .psd-overlay-close {
        background: none;
        border: none;
        color: #fff;
        font-size: 20px;
        cursor: pointer;
        padding: 4px 8px;
        border-radius: 4px;
      }
      
      .psd-overlay-close:hover {
        background: rgba(255,255,255,0.2);
      }
      
      .psd-overlay-content {
        padding: 16px;
        max-height: 500px;
        overflow-y: auto;
      }
      
      .psd-battle-section {
        margin-bottom: 16px;
      }
      
      .psd-section-title {
        font-size: 12px;
        color: #3498db;
        text-transform: uppercase;
        margin-bottom: 8px;
        font-weight: bold;
      }
      
      .psd-pokemon-card {
        display: flex;
        align-items: center;
        padding: 10px;
        background: rgba(255,255,255,0.05);
        border-radius: 8px;
        margin-bottom: 8px;
      }
      
      .psd-pokemon-icon {
        width: 40px;
        height: 40px;
        background: #2c3e50;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        margin-right: 12px;
      }
      
      .psd-pokemon-info {
        flex: 1;
      }
      
      .psd-pokemon-name {
        font-weight: bold;
        font-size: 14px;
      }
      
      .psd-pokemon-hp {
        font-size: 12px;
        color: #7f8c8d;
      }
      
      .psd-hp-bar {
        width: 100%;
        height: 6px;
        background: #2c3e50;
        border-radius: 3px;
        margin-top: 4px;
        overflow: hidden;
      }
      
      .psd-hp-fill {
        height: 100%;
        transition: width 0.3s ease;
      }
      
      .psd-hp-high { background: #2ecc71; }
      .psd-hp-medium { background: #f1c40f; }
      .psd-hp-low { background: #e74c3c; }
      
      .psd-status-badge {
        font-size: 10px;
        padding: 2px 6px;
        border-radius: 4px;
        margin-left: 8px;
      }
      
      .psd-status-burned { background: #e74c3c; }
      .psd-status-poisoned { background: #9b59b6; }
      .psd-status-sleep { background: #3498db; }
      .psd-status-paralyzed { background: #f39c12; }
      
      .psd-recommendation {
        display: flex;
        align-items: center;
        padding: 12px;
        margin: 8px 0;
        background: rgba(52, 152, 219, 0.15);
        border: 1px solid #3498db;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;
      }
      
      .psd-recommendation:hover {
        background: rgba(52, 152, 219, 0.3);
        transform: translateX(4px);
      }
      
      .psd-recommendation-rank {
        width: 28px;
        height: 28px;
        background: #3498db;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        font-weight: bold;
        margin-right: 12px;
      }
      
      .psd-recommendation-info {
        flex: 1;
      }
      
      .psd-recommendation-move {
        font-weight: bold;
        color: #fff;
        font-size: 14px;
      }
      
      .psd-recommendation-reason {
        font-size: 11px;
        color: #bdc3c7;
        margin-top: 2px;
      }
      
      .psd-history-section {
        border-top: 1px solid rgba(255,255,255,0.1);
        padding-top: 12px;
        margin-top: 12px;
      }
      
      .psd-history-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 6px 0;
        font-size: 12px;
        border-bottom: 1px solid rgba(255,255,255,0.05);
      }
      
      .psd-history-icon {
        font-size: 14px;
      }
      
      .psd-history-text {
        color: #ecf0f1;
      }
    `;
    document.head.appendChild(styles);
  }

  setupMessageListeners() {
    chrome.runtime.onMessage.addListener((message) => {
      if (message.type === 'STATE_UPDATED') {
        this.updateFromState(message.data);
      }
    });
  }

  updateFromState(state) {
    if (!state) return;
    
    this.element.innerHTML = `
      <div class="psd-overlay-header">
        <h3>🎮 PSD Assistant</h3>
        <button class="psd-overlay-close" onclick="window.psdOverlay?.hide()">×</button>
      </div>
      <div class="psd-overlay-content">
        <div class="psd-battle-section">
          <div class="psd-section-title">Tu Pokemon</div>
          ${this.renderPokemon(state.myPokemon)}
        </div>
        
        <div class="psd-battle-section">
          <div class="psd-section-title">Pokemon Enemigo</div>
          ${this.renderPokemon(state.enemyPokemon)}
        </div>
        
        ${state.recommendations ? `
        <div class="psd-battle-section">
          <div class="psd-section-title">Recomendaciones</div>
          ${state.recommendations.map((rec, i) => this.renderRecommendation(rec, i + 1)).join('')}
        </div>
        ` : ''}
        
        <div class="psd-history-section">
          <div class="psd-section-title">Historial Reciente</div>
          ${this.renderHistory(state.recentActions || [])}
        </div>
      </div>
    `;
  }

  renderPokemon(pokemon) {
    if (!pokemon) return '<div class="psd-pokemon-card">Sin Pokemon activo</div>';
    
    const hpClass = pokemon.hpPercent >= 50 ? 'psd-hp-high' : 
                    pokemon.hpPercent >= 25 ? 'psd-hp-medium' : 'psd-hp-low';
    
    return `
      <div class="psd-pokemon-card">
        <div class="psd-pokemon-icon">⚔️</div>
        <div class="psd-pokemon-info">
          <div class="psd-pokemon-name">
            ${pokemon.name || 'Unknown'}
            ${pokemon.status ? `<span class="psd-status-badge psd-status-${pokemon.status}">${pokemon.status}</span>` : ''}
          </div>
          <div class="psd-pokemon-hp">${pokemon.hp || 0}/${pokemon.maxHp || 100}</div>
          <div class="psd-hp-bar">
            <div class="psd-hp-fill ${hpClass}" style="width: ${pokemon.hpPercent || 100}%"></div>
          </div>
        </div>
      </div>
    `;
  }

  renderRecommendation(rec, rank) {
    return `
      <div class="psd-recommendation">
        <div class="psd-recommendation-rank">${rank}</div>
        <div class="psd-recommendation-info">
          <div class="psd-recommendation-move">${rec.move}</div>
          <div class="psd-recommendation-reason">${rec.reason || ''}</div>
        </div>
      </div>
    `;
  }

  renderHistory(actions) {
    if (!actions.length) return '<div style="color: #7f8c8d; font-size: 12px;">Sin acciones recientes</div>';
    
    return actions.slice(-5).reverse().map(action => `
      <div class="psd-history-item">
        <span class="psd-history-icon">${this.getActionIcon(action.type)}</span>
        <span class="psd-history-text">${action.description}</span>
      </div>
    `).join('');
  }

  getActionIcon(type) {
    const icons = {
      'switch': '🔄',
      'move': '⚔️',
      'damage': '💥',
      'faint': '💀',
      'status': '💫'
    };
    return icons[type] || '📋';
  }

  show() {
    this.element.style.display = 'block';
    this.isVisible = true;
  }

  hide() {
    this.element.style.display = 'none';
    this.isVisible = false;
  }

  toggle() {
    this.isVisible ? this.hide() : this.show();
  }
}

window.psdOverlay = new OverlayPanel();