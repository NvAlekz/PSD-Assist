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

// ==================== ESTADO ====================
let overlay = null;
let isInitialized = false;
let currentBattleState = null;
let overlayVisible = true;

// ==================== UTILIDADES ====================
function log(message, data = null) {
  if (CONFIG.debug) {
    console.log(`%c[PSD] ${message}`, 'color: #00d4ff; font-weight: bold;', data || '');
  }
}

// ==================== METODO DE DETECCIÓN ====================

function detectBattle() {
  // Verificar si estamos dentro del iframe de batalla
  // El URL del iframe contiene 'battle-' seguido del ID
  
  const url = window.location.href;
  log('URL actual:', url);
  
  // Si la URL contiene 'battle-', estamos en un frame de batalla
  if (url.includes('battle-')) {
    log('Detectado frame de batalla!');
    return extractBattleFromURL(url);
  }
  
  // Si no, buscar iframes de batalla
  const iframes = document.querySelectorAll('iframe');
  log('Iframes encontrados:', iframes.length);
  
  for (const iframe of iframes) {
    if (iframe.src && iframe.src.includes('battle-')) {
      log('Iframe de batalla encontrado:', iframe.src);
      // No podemos acceder al contenido del iframe directamente
      // pero podemos extraer info de la URL
      return extractBattleFromURL(iframe.src);
    }
  }
  
  return null;
}

function extractBattleFromURL(url) {
  // La URL del iframe tiene formato como:
  // https://play.pokemonshowdown.com/battle-gen9ou-1234567890
  const match = url.match(/battle-([a-z]+)-(\d+)/);
  if (match) {
    return {
      format: match[1],
      battleId: match[2],
      hasBattle: true,
      isInBattleFrame: true
    };
  }
  return null;
}

function scanBattle() {
  const state = {
    hasBattle: false,
    myPokemon: null,
    enemyPokemon: null,
    turn: 0,
    detected: false,
    isInBattleFrame: false
  };
  
  // Verificar si estamos en el frame de batalla
  const url = window.location.href;
  
  if (url.includes('battle-')) {
    state.isInBattleFrame = true;
    log('Estamos en el frame de batalla!');
    
    // Intentar extraer datos del DOM del iframe
    // Los elementos de PS están renderizados con classes específicas
    
    // Buscar el campo de batalla
    const battle = document.querySelector('.battle');
    if (!battle) {
      log('No se encontró .battle en el DOM');
      log('Elementos del DOM:', {
        all: document.querySelectorAll('*').length,
        divs: document.querySelectorAll('div').length,
        classes: [...new Set([...document.querySelectorAll('[class]')].map(el => el.className).filter(c => c))]
          .slice(0, 20)
      });
      return state;
    }
    
    // Encontrar los lados de la batalla
    const leftSide = battle.querySelector('.left');
    const rightSide = battle.querySelector('.right');
    
    if (leftSide) {
      state.myPokemon = extractPokemonFromElement(leftSide);
      log('Pokemon mío:', state.myPokemon);
    }
    
    if (rightSide) {
      state.enemyPokemon = extractPokemonFromElement(rightSide);
      log('Pokemon enemigo:', state.enemyPokemon);
    }
    
    state.hasBattle = true;
    state.detected = !!(state.myPokemon || state.enemyPokemon);
  } else {
    // Estamos en el frame principal - buscar iframes
    log('Estamos en el frame principal');
    const iframes = document.querySelectorAll('iframe');
    log('Total iframes:', iframes.length);
    
    for (const iframe of iframes) {
      log('Iframe src:', iframe.src);
      if (iframe.src.includes('battle-')) {
        // Extraer info de la URL del iframe
        state.hasBattle = true;
        state.isInBattleFrame = true;
        
        // Intentar comunicarse con el iframe via postMessage
        try {
          iframe.contentWindow.postMessage({
            type: 'PSD_GET_BATTLE_STATE'
          }, '*');
        } catch (e) {
          log('No se pudo enviar mensaje al iframe');
        }
      }
    }
    
    // Debug info
    log('Estado del documento:', {
      url: window.location.href,
      readyState: document.readyState,
      bodyChildren: document.body ? document.body.children.length : 0
    });
  }
  
  return state;
}

function extractPokemonFromElement(element) {
  if (!element) return null;
  
  // Buscar el nombre - PS usa .name para el nombre del pokemon
  let name = '';
  
  // Intentar múltiples selectores
  const selectors = [
    '.name',
    '.pokename',
    '[data-name]',
    '.pokemonname'
  ];
  
  for (const selector of selectors) {
    const el = element.querySelector(selector);
    if (el && el.textContent) {
      name = el.textContent.trim();
      if (name) break;
    }
  }
  
  // Si no hay nombre, buscar en el title o alt del sprite
  if (!name) {
    const sprite = element.querySelector('.sprite, .pokemonicon, img');
    if (sprite) {
      name = sprite.getAttribute('title') || sprite.getAttribute('alt') || '';
    }
  }
  
  // Limpiar nombre
  name = name.replace(/^(Mega|Alola|Galar|Dynamax|Prime|Z)-?\s*/i, '');
  
  if (!name) return null;
  
  // Buscar HP - PS tiene la barra de HP con el HP en el title
  let hp = 100, maxHp = 100;
  
  const hpBar = element.querySelector('.hpbar, .hptext');
  if (hpBar) {
    const title = hpBar.getAttribute('title') || hpBar.textContent || '';
    log('HP bar title:', title);
    
    // El formato de PS es "XXX/YYY"
    const match = title.match(/(\d+)\s*\/\s*(\d+)/);
    if (match) {
      hp = parseInt(match[1]) || 0;
      maxHp = parseInt(match[2]) || hp;
    }
  }
  
  // Buscar estado (brn, psn, tox, slp, frz, par)
  let status = null;
  const statusEl = element.querySelector('.status');
  if (statusEl && statusEl.textContent) {
    const statusText = statusEl.textContent.toLowerCase().trim();
    if (statusText.includes('brn')) status = 'burned';
    else if (statusText.includes('psn')) status = 'poisoned';
    else if (statusText.includes('tox')) status = 'toxic';
    else if (statusText.includes('slp')) status = 'sleep';
    else if (statusText.includes('frz')) status = 'frozen';
    else if (statusText.includes('par')) status = 'paralyzed';
  }
  
  return {
    name,
    species: name.split(' ')[0],
    hp,
    maxHp,
    hpPercent: maxHp > 0 ? Math.round((hp / maxHp) * 100) : 100,
    status,
    fainted: hp === 0
  };
}

// ==================== LISTENER PARA MENSAJES DEL IFRAME ====================
window.addEventListener('message', (event) => {
  log('Mensaje recibido:', event.data);
  
  if (event.data && event.data.type === 'PSD_BATTLE_STATE') {
    currentBattleState = event.data.state;
    updateOverlay(event.data.state);
  }
});

// ==================== INICIALIZACIÓN ====================
function init() {
  if (isInitialized) return;
  isInitialized = true;
  
  log('Iniciando Pokemon Showdown Assistant...');
  log('URL:', window.location.href);
  
  // Crear overlay inmediatamente
  createOverlay();
  
  // Configurar mensaje listener
  if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.onMessage) {
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      log('Mensaje de popup recibido:', message && message.type ? message.type : 'unknown');
      
      if (!message || !message.type) {
        sendResponse({ success: false });
        return true;
      }
      
      if (message.type === 'TOGGLE_OVERLAY') {
        toggleOverlay();
        sendResponse({ success: true, visible: true });
      } else if (message.type === 'GET_OVERLAY_STATE') {
        sendResponse({ visible: true });
      } else if (message.type === 'GET_BATTLE_STATE') {
        sendResponse({ state: currentBattleState });
      } else {
        sendResponse({ success: false });
      }
      return true;
    });
    log('Message listener configurado');
  }
  
  // Escanear batalla inmediatamente y luego cada segundo
  scanBattle();
  setInterval(scanBattle, 1000);
  
  log('Extension iniciada correctamente');
}

// INICIAR
init();

function createOverlay() {
  
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

