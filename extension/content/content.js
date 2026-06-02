/**
 * Pokemon Showdown Assistant - Content Script
 * Lee directamente del DOM de Pokemon Showdown y muestra overlay
 */

// ==================== CONFIGURACIÓN ====================
const CONFIG = {
  debug: true,
  showNotifications: true,
  autoShowOverlay: true
};

// ==================== SELECTORES DEL DOM ====================
// Nota: Pokemon Showdown cambia frecuentemente su estructura de DOM
// Estos selectores pueden necesitar actualización

const SELECTORS = {
  // Pokemon activo - intenta múltiples selectores
  myActive: [
    '.battle .left .pokemon',
    '.battle-arena .left .trainer .sprite',
    '.battle .pokemon-left-0',
    '.lchat .pokemon',
  ],
  enemyActive: [
    '.battle .right .pokemon',
    '.battle-arena .right .trainer .sprite',
    '.battle .pokemon-right-0',
    '.rchat .pokemon',
  ],
  // HP bar
  hpBar: '.hpbar, .hp-text, .HPText',
  // Nombre del pokemon
  pokemonName: '.name, .pokename, .PokemonName',
  // Menu de movimientos
  moves: '.movemenu .move, #movemenu .move',
  // Menu de switches
  switches: '.switchmenu .pokemon, #switchmenu .pokemon',
  // Indicador de batalla activa
  battleActive: '.battle, .battle-arena, #battle-bg',
};

// ==================== UTILIDADES ====================

function log(message, data = null) {
  if (CONFIG.debug) {
    console.log(`%c[PSD] ${message}`, 'color: #3498db; font-weight: bold;', data || '');
  }
}

function createOverlay() {
  if (document.getElementById('psd-overlay')) return;
  
  const overlay = document.createElement('div');
  overlay.id = 'psd-overlay';
  overlay.innerHTML = `
    <style>
      #psd-overlay {
        position: fixed;
        top: 10px;
        right: 10px;
        width: 300px;
        max-height: 80vh;
        background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
        border: 2px solid #00d4ff;
        border-radius: 16px;
        color: #fff;
        font-family: 'Segoe UI', -apple-system, sans-serif;
        z-index: 999999;
        box-shadow: 0 8px 32px rgba(0, 212, 255, 0.2);
        overflow: hidden;
        transition: all 0.3s ease;
      }
      
      #psd-overlay.minimized {
        width: 50px;
        height: 50px;
        cursor: pointer;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
      }
      
      #psd-overlay.minimized .psd-content { display: none; }
      
      #psd-header {
        background: linear-gradient(135deg, #0f3460 0%, #00d4ff 100%);
        padding: 12px 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        cursor: move;
      }
      
      #psd-header h3 {
        margin: 0;
        font-size: 14px;
        display: flex;
        align-items: center;
        gap: 8px;
      }
      
      .psd-pokemon-icon {
        width: 36px;
        height: 36px;
        background: rgba(255,255,255,0.2);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      
      .psd-controls {
        display: flex;
        gap: 8px;
      }
      
      .psd-btn {
        background: rgba(255,255,255,0.1);
        border: none;
        color: #fff;
        width: 28px;
        height: 28px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 14px;
        transition: background 0.2s;
      }
      
      .psd-btn:hover {
        background: rgba(255,255,255,0.25);
      }
      
      #psd-content {
        padding: 12px;
        max-height: 400px;
        overflow-y: auto;
      }
      
      .psd-section {
        margin-bottom: 16px;
      }
      
      .psd-section-title {
        font-size: 11px;
        color: #00d4ff;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
        font-weight: 600;
      }
      
      .psd-card {
        background: rgba(255,255,255,0.05);
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 8px;
      }
      
      .psd-card-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 8px;
      }
      
      .psd-card-icon {
        width: 32px;
        height: 32px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
      }
      
      .psd-card-icon.enemy {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
      }
      
      .psd-card-name {
        font-weight: 600;
        font-size: 14px;
      }
      
      .psd-card-status {
        font-size: 10px;
        padding: 2px 6px;
        border-radius: 4px;
        margin-left: 6px;
      }
      
      .psd-status-burned { background: #e74c3c; }
      .psd-status-poisoned { background: #9b59b6; }
      .psd-status-sleep { background: #3498db; }
      .psd-status-paralyzed { background: #f1c40f; color: #000; }
      
      .psd-hp-container {
        display: flex;
        align-items: center;
        gap: 8px;
      }
      
      .psd-hp-text {
        font-size: 12px;
        color: #888;
        min-width: 60px;
      }
      
      .psd-hp-bar {
        flex: 1;
        height: 8px;
        background: #2a2a4a;
        border-radius: 4px;
        overflow: hidden;
      }
      
      .psd-hp-fill {
        height: 100%;
        transition: width 0.5s ease, background 0.3s;
      }
      
      .psd-hp-high { background: linear-gradient(90deg, #00b894, #00cec9); }
      .psd-hp-medium { background: linear-gradient(90deg, #fdcb6e, #f39c12); }
      .psd-hp-low { background: linear-gradient(90deg, #ff7675, #d63031); }
      
      .psd-recommendation {
        background: rgba(0, 212, 255, 0.1);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 10px;
        padding: 10px 12px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 10px;
        cursor: pointer;
        transition: all 0.2s;
      }
      
      .psd-recommendation:hover {
        background: rgba(0, 212, 255, 0.2);
        transform: translateX(4px);
      }
      
      .psd-recommendation-rank {
        width: 24px;
        height: 24px;
        background: #00d4ff;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 12px;
        color: #000;
      }
      
      .psd-recommendation-info {
        flex: 1;
      }
      
      .psd-recommendation-move {
        font-weight: 600;
        font-size: 13px;
      }
      
      .psd-recommendation-reason {
        font-size: 11px;
        color: #00d4ff;
        margin-top: 2px;
      }
      
      .psd-footer {
        background: rgba(0,0,0,0.3);
        padding: 8px 16px;
        font-size: 11px;
        color: #666;
        text-align: center;
      }
      
      .psd-debug {
        font-size: 10px;
        color: #666;
        margin-top: 4px;
      }
      
      .psd-no-battle {
        text-align: center;
        padding: 40px 20px;
        color: #888;
      }
      
      .psd-no-battle-icon {
        font-size: 48px;
        margin-bottom: 16px;
      }
    </style>
    
    <div id="psd-header">
      <h3>⚡ PSD Assistant</h3>
      <div class="psd-controls">
        <button class="psd-btn" id="psd-minimize" title="Minimizar">−</button>
        <button class="psd-btn" id="psd-close" title="Cerrar">×</button>
      </div>
    </div>
    
    <div id="psd-content">
      <div class="psd-no-battle">
        <div class="psd-no-battle-icon">🎮</div>
        <div>Iniciando...</div>
        <div class="psd-debug">Esperando batalla de Pokemon Showdown</div>
      </div>
    </div>
    
    <div class="psd-footer">Pokemon Showdown Assistant v1.0</div>
  `;
  
  document.body.appendChild(overlay);
  
  // Event listeners para los botones
  document.getElementById('psd-minimize').addEventListener('click', () => {
    overlay.classList.toggle('minimized');
  });
  
  document.getElementById('psd-close').addEventListener('click', () => {
    overlay.style.display = 'none';
  });
  
  log('Overlay creado');
  return overlay;
}

function updateOverlay(state) {
  const overlay = document.getElementById('psd-overlay');
  if (!overlay) return;
  
  const content = document.getElementById('psd-content');
  
  if (!state || !state.hasBattle) {
    content.innerHTML = `
      <div class="psd-no-battle">
        <div class="psd-no-battle-icon">🎮</div>
        <div>Esperando batalla...</div>
        <div class="psd-debug">Ingresa a una batalla en Pokemon Showdown</div>
      </div>
    `;
    return;
  }
  
  // Renderizar estado de la batalla
  content.innerHTML = `
    <div class="psd-section">
      <div class="psd-section-title">Tu Pokemon</div>
      ${renderPokemonCard(state.myPokemon, false)}
    </div>
    
    <div class="psd-section">
      <div class="psd-section-title">Pokemon Enemigo</div>
      ${renderPokemonCard(state.enemyPokemon, true)}
    </div>
    
    ${state.recommendations && state.recommendations.length > 0 ? `
    <div class="psd-section">
      <div class="psd-section-title">Recomendaciones</div>
      ${state.recommendations.map((rec, i) => `
        <div class="psd-recommendation">
          <div class="psd-recommendation-rank">${i + 1}</div>
          <div class="psd-recommendation-info">
            <div class="psd-recommendation-move">${rec.move || rec.name || 'Mover'}</div>
            <div class="psd-recommendation-reason">${rec.reason || rec.description || 'Opción recomendada'}</div>
          </div>
        </div>
      `).join('')}
    </div>
    ` : ''}
    
    <div class="psd-section">
      <div class="psd-section-title">Diagnóstico</div>
      <div class="psd-debug">
        🕐 Turno: ${state.turn || '?'} | 
        📊 Detectado: ${state.detected ? '✓' : '✗'}
      </div>
    </div>
  `;
}

function renderPokemonCard(pokemon, isEnemy = false) {
  if (!pokemon) {
    return '<div class="psd-card"><div class="psd-debug">No detectado</div></div>';
  }
  
  const hpPercent = pokemon.hpPercent || 100;
  const hpClass = hpPercent >= 50 ? 'psd-hp-high' : hpPercent >= 25 ? 'psd-hp-medium' : 'psd-hp-low';
  const statusHtml = pokemon.status ? 
    `<span class="psd-card-status psd-status-${pokemon.status}">${pokemon.status}</span>` : '';
  
  return `
    <div class="psd-card">
      <div class="psd-card-header">
        <div class="psd-card-icon ${isEnemy ? 'enemy' : ''}">
          ${isEnemy ? '👹' : '⚔️'}
        </div>
        <div class="psd-card-name">
          ${pokemon.name || pokemon.species || 'Unknown'}
          ${statusHtml}
        </div>
      </div>
      <div class="psd-hp-container">
        <span class="psd-hp-text">${pokemon.hp || 0}/${pokemon.maxHp || 100} HP</span>
        <div class="psd-hp-bar">
          <div class="psd-hp-fill ${hpClass}" style="width: ${hpPercent}%"></div>
        </div>
      </div>
    </div>
  `;
}

// ==================== PARSER DEL DOM ====================

function scanBattle() {
  const state = {
    hasBattle: false,
    myPokemon: null,
    enemyPokemon: null,
    turn: 0,
    detected: false
  };
  
  // Verificar si hay una batalla activa
  const battleArea = document.querySelector('.battle, .battle-arena, #battle, .left, .right');
  
  if (!battleArea) {
    log('No se detectó área de batalla');
    return state;
  }
  
  state.hasBattle = true;
  
  // Intentar detectar Pokemon activo del jugador
  const myPokemonEl = findElement(SELECTORS.myActive);
  if (myPokemonEl) {
    state.myPokemon = parsePokemonFromElement(myPokemonEl);
    log('Pokemon mío detectado:', state.myPokemon);
  }
  
  // Intentar detectar Pokemon activo del enemigo
  const enemyPokemonEl = findElement(SELECTORS.enemyActive);
  if (enemyPokemonEl) {
    state.enemyPokemon = parsePokemonFromElement(enemyPokemonEl);
    log('Pokemon enemigo detectado:', state.enemyPokemon);
  }
  
  // Contar turnos
  const turnElement = document.querySelector('.turn-count, #turn-count, .battle-turn');
  if (turnElement) {
    state.turn = parseInt(turnElement.textContent) || 0;
  } else {
    // Escanear el log de batalla para contar turnos
    const messages = document.querySelectorAll('.battle-log .message');
    state.turn = Math.ceil(messages.length / 2);
  }
  
  state.detected = !!(state.myPokemon || state.enemyPokemon);
  
  return state;
}

function findElement(selectors) {
  for (const selector of selectors) {
    const el = document.querySelector(selector);
    if (el) return el;
  }
  return null;
}

function parsePokemonFromElement(element) {
  if (!element) return null;
  
  // Extraer nombre
  let name = '';
  const nameEl = element.querySelector('.name, .pokename, [class*="name"]');
  if (nameEl) {
    name = nameEl.textContent.trim();
  }
  
  // Limpiar nombre (remover badges como "Mega ", "Alola ", etc.)
  name = name.replace(/^(Mega|Alola|Galar|Dynamax|Prime|Z)-?\s*/i, '');
  
  // Extraer HP
  let hp = 100, maxHp = 100;
  const hpBar = element.querySelector('.hpbar, .hp-text, [class*="hpbar"]');
  if (hpBar) {
    const hpText = hpBar.textContent || hpBar.dataset?.hp || '';
    const match = hpText.match(/(\d+)\s*\/?\s*(\d*)/);
    if (match) {
      hp = parseInt(match[1]) || 0;
      maxHp = parseInt(match[2]) || hp;
    }
  }
  
  // Calcular porcentaje
  const hpPercent = maxHp > 0 ? Math.round((hp / maxHp) * 100) : 100;
  
  // Detectar estado
  let status = null;
  const statusEl = element.querySelector('.status, [class*="status"]');
  if (statusEl && !statusEl.classList.contains('status-container')) {
    const statusText = statusEl.textContent.toLowerCase();
    if (statusText.includes('brn') || statusText.includes('burn')) status = 'burned';
    else if (statusText.includes('psn') || statusText.includes('poison')) status = 'poisoned';
    else if (statusText.includes('tox') || statusText.includes('toxic')) status = 'toxic';
    else if (statusText.includes('slp') || statusText.includes('sleep')) status = 'sleep';
    else if (statusText.includes('frz') || statusText.includes('freeze')) status = 'frozen';
    else if (statusText.includes('par') || statusText.includes('paral')) status = 'paralyzed';
  }
  
  // Verificar si está debilitado
  const fainted = hp === 0 || element.classList.contains('fainted');
  
  return {
    name,
    species: name.split(' ')[0],
    hp,
    maxHp,
    hpPercent,
    status,
    fainted
  };
}

// ==================== INICIALIZACIÓN ====================

let overlay = null;
let lastState = null;
let overlayVisible = true;

function init() {
  log('Iniciando Pokemon Showdown Assistant...');
  
  // Crear overlay
  overlay = createOverlay();
  
  // Escanear periódicamente
  const scanInterval = setInterval(() => {
    const state = scanBattle();
    
    if (state.hasBattle && (state.myPokemon || state.enemyPokemon)) {
      updateOverlay(state);
      
      // Notificar si hubo cambios significativos
      if (CONFIG.showNotifications && lastState) {
        if (state.myPokemon?.hpPercent !== lastState.myPokemon?.hpPercent) {
          log('HP cambió:', state.myPokemon?.hpPercent);
        }
      }
      
      lastState = state;
    }
  }, 1000); // Escanear cada segundo
  
  log('Extension iniciada correctamente');
}

// Escuchar mensajes del background/popup
if (typeof chrome !== 'undefined' && chrome.runtime) {
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    log('Mensaje recibido:', message.type);
    
    if (message.type === 'TOGGLE_OVERLAY') {
      toggleOverlay();
      sendResponse({ success: true });
    } else if (message.type === 'GET_OVERLAY_STATE') {
      sendResponse({ visible: overlayVisible });
    } else if (message.type === 'STATE_UPDATED') {
      // Refrescar datos si es necesario
      log('Estado actualizado');
      sendResponse({ success: true });
    } else {
      sendResponse({ success: false });
    }
    
    return true;
  });
}

function toggleOverlay() {
  const overlayEl = document.getElementById('psd-overlay');
  if (overlayEl) {
    if (overlayVisible) {
      overlayEl.style.display = 'none';
      overlayVisible = false;
    } else {
      overlayEl.style.display = 'block';
      overlayVisible = true;
    }
    log('Overlay toggled:', overlayVisible);
  }
}

// Iniciar cuando el DOM esté listo
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}