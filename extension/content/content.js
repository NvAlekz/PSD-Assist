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
// Pokemon Showdown usa iframes y JavaScript dinámico para renderizar batallas
// NO usa selectores CSS tradicionales - la UI se genera con JS

const SELECTORS = {
  // Iframe de batalla (contenedor principal)
  battleIframe: [
    'iframe[name="battle"]',
    'iframe[title*="battle"]',
    '#battle iframe',
    '.battle-iframe'
  ],
  
  // Buscar cualquier cosa relacionada con la batalla
  battleContainer: [
    '.battle',
    '#battle',
    '[id*="battle"]'
  ],
  
  // Cuando el menu de team preview está activo
  teamPreview: [
    '.teampreview',
    '#teampreview',
    '.chooseteam'
  ]
};

// ==================== UTILIDADES ====================

function log(message, data = null) {
  if (CONFIG.debug) {
    console.log(`%c[PSD] ${message}`, 'color: #3498db; font-weight: bold;', data || '');
  }
}

// ==================== METODOS DE DETECCIÓN ====================

// Método 1: Buscar en variables globales de PS
function getBattleStateFromPSGlobals() {
  // PS almacena el estado en window.BattleHistory o similar
  // Esto es lo que usan otras extensiones como Showdex
  
  try {
    // Intentar acceder al estado de PS si está disponible
    if (window.Battle && window.Battle.lastBattle) {
      const battle = window.Battle.lastBattle;
      return {
        myPokemon: battle.p1?.active?.[0] ? parseBattlePokemon(battle.p1.active[0]) : null,
        enemyPokemon: battle.p2?.active?.[0] ? parseBattlePokemon(battle.p2.active[0]) : null,
        hasBattle: true
      };
    }
  } catch (e) {
    log('No se pudo acceder a globals de PS');
  }
  return null;
}

function parseBattlePokemon(poke) {
  if (!poke) return null;
  return {
    name: poke.name || poke.species || 'Unknown',
    species: poke.species || 'Unknown',
    hp: poke.hp || 100,
    maxHp: poke.maxhp || 100,
    hpPercent: poke.hp ? Math.round((poke.hp / poke.maxhp) * 100) : 100,
    status: poke.status || null,
    fainted: poke.fainted || false
  };
}

// Método 2: Buscar en el DOM (menos fiable pero puede funcionar)
function getBattleStateFromDOM() {
  // Verificar si hay iframe de batalla
  const iframe = document.querySelector('iframe[name="battle"], iframe[title*="battle"]');
  
  if (iframe && iframe.contentDocument) {
    // El iframe tiene su propio documento
    const doc = iframe.contentDocument;
    
    // Buscar elementos en el iframe
    const battleArea = doc.querySelector('.battle, .left, .right');
    if (battleArea) {
      log('Batalla encontrada en iframe');
      return {
        myPokemon: parsePokemonFromDOM(doc, '.left'),
        enemyPokemon: parsePokemonFromDOM(doc, '.right'),
        hasBattle: true
      };
    }
  }
  
  // Buscar en el documento principal
  const mainBattle = document.querySelector('.battle');
  if (mainBattle) {
    return {
      myPokemon: parsePokemonFromDOM(document, '.left'),
      enemyPokemon: parsePokemonFromDOM(document, '.right'),
      hasBattle: true
    };
  }
  
  return null;
}

function parsePokemonFromDOM(doc, side) {
  // Esta función intenta parsear Pokemon del DOM
  // Los selectores pueden variar según la versión de PS
  const container = doc.querySelector(side);
  if (!container) return null;
  
  // Intentar múltiples formas de encontrar el nombre
  let name = '';
  const nameEl = container.querySelector('.name, .pokename, [data-name]');
  if (nameEl) {
    name = nameEl.textContent.trim();
  }
  
  // HP bar
  let hp = 100, maxHp = 100;
  const hpBar = container.querySelector('.hpbar, .hp-text');
  if (hpBar) {
    const hpText = hpBar.textContent || hpBar.dataset?.hp || '';
    const match = hpText.match(/(\d+)\s*\/?\s*(\d*)/);
    if (match) {
      hp = parseInt(match[1]) || 0;
      maxHp = parseInt(match[2]) || hp;
    }
  }
  
  if (!name) return null;
  
  return {
    name: name.replace(/^(Mega|Alola|Galar|Dynamax|Prime|Z)-?\s*/i, ''),
    species: name.split(' ')[0],
    hp,
    maxHp,
    hpPercent: maxHp > 0 ? Math.round((hp / maxHp) * 100) : 100,
    status: null,
    fainted: hp === 0
  };
}

// Método 3: Buscar en mensajes del cliente (si PS expone los mensajes)
function getBattleStateFromClientMessages() {
  // Algunos datos pueden estar en variables globales del cliente
  // Esto es especulativo pero puede funcionar
  try {
    // Intentar acceder a clientVars o similar
    if (window.clientVars && window.clientVars.user) {
      log('clientVars detectado');
    }
  } catch (e) {}
  return null;
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
  
  // MÉTODO 1: Intentar acceder al iframe de batalla
  try {
    const iframe = document.querySelector('iframe[name="battle"]');
    if (iframe && iframe.contentDocument) {
      const iframeDoc = iframe.contentDocument;
      const battleInIframe = iframeDoc.querySelector('.battle');
      if (battleInIframe) {
        log('Batalla detectada en iframe');
        
        // Intentar extraer datos del iframe
        const leftSide = iframeDoc.querySelector('.left');
        const rightSide = iframeDoc.querySelector('.right');
        
        if (leftSide) {
          state.myPokemon = extractPokemonFromSide(leftSide);
        }
        if (rightSide) {
          state.enemyPokemon = extractPokemonFromSide(rightSide);
        }
        
        if (state.myPokemon || state.enemyPokemon) {
          state.hasBattle = true;
          state.detected = true;
          return state;
        }
      }
    }
  } catch (e) {
    log('Error accediendo al iframe:', e.message);
  }
  
  // MÉTODO 2: Buscar en el documento principal
  const mainBattle = document.querySelector('.battle');
  if (mainBattle) {
    log('Batalla detectada en documento principal');
    
    const leftSide = document.querySelector('.left');
    const rightSide = document.querySelector('.right');
    
    if (leftSide) {
      state.myPokemon = extractPokemonFromSide(leftSide);
    }
    if (rightSide) {
      state.enemyPokemon = extractPokemonFromSide(rightSide);
    }
    
    if (state.myPokemon || state.enemyPokemon) {
      state.hasBattle = true;
      state.detected = true;
      return state;
    }
  }
  
  // MÉTODO 3: Buscar si hay URL de batalla en el iframe
  const battleIframes = document.querySelectorAll('iframe');
  for (const iframe of battleIframes) {
    if (iframe.src && iframe.src.includes('battle')) {
      log('Iframe de batalla encontrado:', iframe.src);
      state.hasBattle = true;
    }
  }
  
  // MÉTODO 4: Verificar si hay elementos de team preview (batalla iniciada)
  const teamPreview = document.querySelector('.teampreview, .chooseteam');
  if (teamPreview) {
    log('Team preview detectado - batalla iniciada');
    state.hasBattle = true;
    state.detected = true;
  }
  
  // Debug: mostrar conteo de elementos
  log('Elementos encontrados:', {
    battle: document.querySelectorAll('.battle').length,
    left: document.querySelectorAll('.left').length,
    right: document.querySelectorAll('.right').length,
    iframeBattle: document.querySelectorAll('iframe[name="battle"]').length,
    iframesTotal: document.querySelectorAll('iframe').length
  });
  
  return state;
}

function extractPokemonFromSide(side) {
  if (!side) return null;
  
  // Buscar nombre del pokemon
  let name = '';
  const nameEl = side.querySelector('.name, .pokename');
  if (nameEl) {
    name = nameEl.textContent.trim();
  }
  
  // Si no hay nombre, buscar en otros lugares
  if (!name) {
    const allElements = side.querySelectorAll('*');
    for (const el of allElements) {
      // Buscar texto que parezca nombre de pokemon
      const text = el.textContent.trim();
      if (text && text.length > 2 && text.length < 20 && !text.includes(' ')) {
        // Podría ser un nombre de pokemon
        name = text;
        break;
      }
    }
  }
  
  if (!name) return null;
  
  // Limpiar nombre
  name = name.replace(/^(Mega|Alola|Galar|Dynamax|Prime|Z)-?\s*/i, '');
  
  // Buscar HP
  let hp = 100, maxHp = 100;
  const hpBar = side.querySelector('.hpbar');
  if (hpBar) {
    // El HP puede estar en dataset o en texto
    const hpText = hpBar.dataset?.hp || hpBar.textContent || '';
    const match = hpText.match(/(\d+)\s*\/?\s*(\d*)/);
    if (match) {
      hp = parseInt(match[1]) || 0;
      maxHp = parseInt(match[2]) || hp;
    }
  }
  
  return {
    name,
    species: name.split(' ')[0],
    hp,
    maxHp,
    hpPercent: maxHp > 0 ? Math.round((hp / maxHp) * 100) : 100,
    status: null,
    fainted: hp === 0
  };
}



// ==================== INICIALIZACIÓN ====================

let overlay = null;
let lastState = null;
let overlayVisible = true;
let isInitialized = false;

function init() {
  if (isInitialized) return;
  isInitialized = true;
  
  log('Iniciando Pokemon Showdown Assistant...');
  
  // Crear overlay inmediatamente
  createOverlay();
  
  // Configurar mensaje listener
  if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.onMessage) {
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      log('Mensaje recibido:', message && message.type ? message.type : 'unknown');
      
      if (!message || !message.type) {
        sendResponse({ success: false });
        return true;
      }
      
      if (message.type === 'TOGGLE_OVERLAY') {
        toggleOverlay();
        sendResponse({ success: true, visible: overlayVisible });
      } else if (message.type === 'GET_OVERLAY_STATE') {
        sendResponse({ visible: overlayVisible });
      } else {
        sendResponse({ success: false });
      }
      return true;
    });
    log('Message listener configurado');
  } else {
    log('Chrome runtime no disponible');
  }
  
  // Escanear periódicamente
  setInterval(() => {
    const state = scanBattle();
    if (state.hasBattle) {
      updateOverlay(state);
      lastState = state;
    }
  }, 1000);
  
  log('Extension iniciada correctamente');
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

// INICIAR INMEDIATAMENTE
init();