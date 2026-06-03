/**
 * Pokemon Showdown Assistant - Content Script
 * Detecta batallas en Pokemon Showdown SPA
 */

(function() {
  'use strict';

  // ==================== CONFIGURACIÓN ====================
  const CONFIG = {
    debug: true,
    scanInterval: 500,  // Escaneo más frecuente
    maxWaitForDOM: 5000 // Tiempo máximo esperando elementos del DOM
  };

  // ==================== ESTADO ====================
  let isInitialized = false;
  let currentBattleState = null;
  let scanCount = 0;
  let lastUrl = '';

  // ==================== UTILIDADES ====================
  function log(message, data) {
    if (CONFIG.debug) {
      console.log('[PSD] ' + message, data !== undefined ? data : '');
    }
  }

  // ==================== DETECCIÓN DE URL ====================
  function analyzeURL() {
    const url = window.location.href;
    const pathname = window.location.pathname;
    const search = window.location.search;
    
    log('=== ANÁLISIS DE URL ===');
    log('href:', url);
    log('pathname:', pathname);
    log('search:', search);
    
    // Detectar diferentes tipos de vistas en PS
    const isBattleRoom = pathname.includes('/battle-');
    const isBattleRoomAlt = url.includes('/battle-');
    const roomMatch = url.match(/\/([a-z0-9-]+)-[a-z0-9]{10,}/i);
    const isRoomView = roomMatch && !isBattleRoom && !pathname.includes('/');
    
    log('¿battle- en URL?:', isBattleRoom || isBattleRoomAlt);
    log('¿Room view?:', isRoomView, 'Room:', roomMatch ? roomMatch[1] : null);
    
    return {
      url: url,
      pathname: pathname,
      isBattleRoom: isBattleRoom || isBattleRoomAlt,
      isRoomView: isRoomView,
      roomName: roomMatch ? roomMatch[1] : null
    };
  }

  // ==================== DETECCIÓN DE ELEMENTOS DEL DOM ====================
  function analyzeDOM() {
    log('=== ANÁLISIS DEL DOM ===');
    
    // Elementos de batalla
    const battleCount = document.querySelectorAll('.battle').length;
    const leftCount = document.querySelectorAll('.left').length;
    const rightCount = document.querySelectorAll('.right').length;
    const battleLogCount = document.querySelectorAll('.battle-log').length;
    const turnCount = document.querySelectorAll('.turn-count, [class*="turn"]').length;
    
    // Elementos de sala/página
    const roomCount = document.querySelectorAll('.room').length;
    const chatCount = document.querySelectorAll('.chat').length;
    const iframeCount = document.querySelectorAll('iframe').length;
    
    // Estados de la página
    const readyState = document.readyState;
    const bodyChildren = document.body ? document.body.children.length : 0;
    
    log('Elementos encontrados:');
    log('  .battle:', battleCount);
    log('  .left:', leftCount);
    log('  .right:', rightCount);
    log('  .battle-log:', battleLogCount);
    log('  .turn:', turnCount);
    log('  .room:', roomCount);
    log('  .chat:', chatCount);
    log('  iframes:', iframeCount);
    log('  readyState:', readyState);
    log('  body children:', bodyChildren);
    
    // Analizar clases únicas en el documento
    const allElements = document.querySelectorAll('[class]');
    const classSet = new Set();
    allElements.forEach(function(el) {
      el.classList.forEach(function(c) {
        if (c.includes('battle') || c.includes('room') || c.includes('chat') || c.includes('turn')) {
          classSet.add(c);
        }
      });
    });
    log('Clases relevantes:', [...classSet]);
    
    return {
      battle: battleCount,
      left: leftCount,
      right: rightCount,
      battleLog: battleLogCount,
      turn: turnCount,
      room: roomCount,
      chat: chatCount,
      iframe: iframeCount,
      readyState: readyState
    };
  }

  // ==================== SCAN DE BATALLA ====================
  function scanBattle() {
    scanCount++;
    const urlInfo = analyzeURL();
    const domInfo = analyzeDOM();
    
    const state = {
      hasBattle: false,
      myPokemon: null,
      enemyPokemon: null,
      turn: 0,
      detected: false,
      scanCount: scanCount,
      urlInfo: urlInfo,
      domInfo: domInfo
    };

    // Caso 1: Estamos en una sala de batalla (URL con /battle-)
    if (urlInfo.isBattleRoom) {
      log('=== MODO BATALLA: URL contiene /battle- ===');
      
      // Esperar que el DOM de batalla se cargue
      const battle = document.querySelector('.battle');
      
      if (!battle) {
        log('⚠️ No se encontró .battle - esperando que cargue');
        // Posiblemente aún se está cargando
        // Verificar si hay otros indicadores
        const bodyHTML = document.body ? document.body.innerHTML.substring(0, 500) : 'sin body';
        log('Primeros 500 chars del body:', bodyHTML);
        return state;
      }
      
      log('✓ .battle encontrado!');
      state.hasBattle = true;
      
      // Buscar lados de la batalla
      const leftSide = battle.querySelector('.left');
      const rightSide = battle.querySelector('.right');
      
      if (leftSide) {
        log('✓ .left encontrado');
        state.myPokemon = extractPokemon(leftSide);
        log('Pokemon mío:', state.myPokemon);
      } else {
        log('✗ .left no encontrado');
      }
      
      if (rightSide) {
        log('✓ .right encontrado');
        state.enemyPokemon = extractPokemon(rightSide);
        log('Pokemon enemigo:', state.enemyPokemon);
      } else {
        log('✗ .right no encontrado');
      }
      
      // Buscar turno
      const turnEl = battle.querySelector('.turn-count, [class*="turn"]');
      if (turnEl) {
        state.turn = parseInt(turnEl.textContent) || 0;
        log('Turno:', state.turn);
      }
      
      state.detected = !!(state.myPokemon || state.enemyPokemon);
      log('¿Detectado?:', state.detected);
      
      return state;
    }
    
    // Caso 2: Estamos en una sala de chat (room view)
    if (urlInfo.isRoomView) {
      log('=== MODO SALA: Detectado room view ===');
      
      const room = document.querySelector('.room');
      if (room) {
        log('✓ .room encontrado');
        
        // Buscar si hay un iframe de batalla dentro
        const iframes = room.querySelectorAll('iframe');
        log('Iframes dentro de .room:', iframes.length);
        
        for (let i = 0; i < iframes.length; i++) {
          log('  Iframe ' + i + ' src:', iframes[i].src);
          if (iframes[i].src && iframes[i].src.includes('battle-')) {
            log('✓ Iframe de batalla encontrado!');
            state.hasBattle = true;
            state.isInIframe = true;
            state.iframeSrc = iframes[i].src;
          }
        }
      }
      
      return state;
    }
    
    // Caso 3: Estamos en la página principal
    log('=== MODO PRINCIPAL: Página de inicio ===');
    
    // Buscar cualquier iframe
    const iframes = document.querySelectorAll('iframe');
    log('Total iframes en página:', iframes.length);
    
    for (let i = 0; i < iframes.length; i++) {
      const src = iframes[i].src || '(sin src)';
      log('  Iframe ' + i + ':', src);
      
      if (src.includes('battle-')) {
        log('✓ Iframe de batalla encontrado en página principal');
        state.hasBattle = true;
        state.isInIframe = true;
        state.iframeSrc = src;
      }
    }
    
    return state;
  }

  // ==================== EXTRAER POKEMON ====================
  function extractPokemon(element) {
    if (!element) return null;

    log('Extrayendo Pokemon de elemento...');

    // Intentar múltiples selectores para el nombre
    let name = '';
    const selectors = ['.name', '.pokename', '[data-name]', '.pokemon-name', '.trainer-name'];
    
    for (let i = 0; i < selectors.length; i++) {
      const el = element.querySelector(selectors[i]);
      if (el && el.textContent) {
        name = el.textContent.trim();
        log('  Selector ' + selectors[i] + ' encontró:', name);
        if (name) break;
      }
    }

    // Si no hay nombre, buscar en atributos del sprite
    if (!name) {
      const sprite = element.querySelector('.sprite, .pokemonicon, .pokémon-sprite, img');
      if (sprite) {
        name = sprite.getAttribute('title') || sprite.getAttribute('alt') || '';
        log('  Sprite title/alt:', name);
      }
    }

    // Limpiar nombre
    name = name.replace(/^(Mega|Alola|Galar|Dynamax|Prime|Z)-?\s*/i, '');
    name = name.split(' ')[0]; // Solo el nombre base
    
    if (!name) {
      log('  ✗ No se pudo extraer nombre');
      return null;
    }

    log('  Nombre extraído:', name);

    // HP
    let hp = 100, maxHp = 100;
    const hpBar = element.querySelector('.hpbar, .hp-text, .hptext, [class*="hpbar"]');
    if (hpBar) {
      const title = hpBar.getAttribute('title') || '';
      const text = hpBar.textContent || '';
      const hpSource = title || text;
      log('  HP source:', hpSource);
      
      const match = hpSource.match(/(\d+)\s*\/?\s*(\d+)/);
      if (match) {
        hp = parseInt(match[1]) || 0;
        maxHp = parseInt(match[2]) || hp;
      }
    }

    return {
      name: name,
      hp: hp,
      maxHp: maxHp,
      hpPercent: maxHp > 0 ? Math.round((hp / maxHp) * 100) : 100,
      status: null,
      fainted: hp === 0
    };
  }

  // ==================== OBSERVER PARA CAMBIOS ====================
  function setupMutationObserver() {
    log('Configurando MutationObserver...');
    
    let debounceTimer = null;
    
    const observer = new MutationObserver(function(mutations) {
      // Debounce para evitar múltiples llamadas
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(function() {
        log('=== MUTATION OBSERVER: Cambio detectado ===');
        const state = scanBattle();
        updateOverlay(state);
      }, 100);
    });

    observer.observe(document.body || document.documentElement, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['class', 'id', 'src']
    });
    
    log('MutationObserver configurado');
  }

  // ==================== LISTENER PARA CAMBIOS DE URL ====================
  function setupHistoryListener() {
    log('Configurando History listener...');
    
    // Interceptar pushState y replaceState
    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;
    
    history.pushState = function() {
      log('=== HISTORY.pushState detectado ===');
      originalPushState.apply(history, arguments);
      setTimeout(function() {
        log('URL cambió a:', window.location.href);
        const state = scanBattle();
        updateOverlay(state);
      }, 100);
    };
    
    history.replaceState = function() {
      log('=== HISTORY.replaceState detectado ===');
      originalReplaceState.apply(history, arguments);
      setTimeout(function() {
        log('URL reemplazada a:', window.location.href);
        const state = scanBattle();
        updateOverlay(state);
      }, 100);
    };
    
    // Listener para popstate (botón atrás/adelante)
    window.addEventListener('popstate', function() {
      log('=== POPSTATE detectado ===');
      log('URL actual:', window.location.href);
      setTimeout(function() {
        const state = scanBattle();
        updateOverlay(state);
      }, 100);
    });
    
    log('History listener configurado');
  }

  // ==================== OVERLAY ====================
  function createOverlay() {
    if (document.getElementById('psd-overlay')) {
      log('Overlay ya existe');
      return;
    }

    const overlay = document.createElement('div');
    overlay.id = 'psd-overlay';
    overlay.innerHTML = 
      '<div style="position:fixed;top:10px;right:10px;width:320px;padding:15px;background:linear-gradient(145deg,#1a1a2e,#16213e);border:2px solid #00d4ff;border-radius:12px;color:#fff;font-family:Segoe UI,sans-serif;z-index:99999;box-shadow:0 4px 20px rgba(0,212,255,0.3);">' +
      '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid rgba(0,212,255,0.3);">' +
      '<h3 style="margin:0;font-size:14px;color:#00d4ff;">⚡ PSD Assistant</h3>' +
      '<button id="psd-close" style="background:rgba(255,255,255,0.1);border:none;color:#fff;width:24px;height:24px;border-radius:4px;cursor:pointer;font-size:16px;">×</button>' +
      '</div>' +
      '<div id="psd-status" style="font-size:12px;line-height:1.5;"></div>' +
      '<div id="psd-debug" style="margin-top:10px;font-size:10px;color:#888;border-top:1px solid rgba(255,255,255,0.1);padding-top:8px;"></div>' +
      '</div>';
    
    document.body.appendChild(overlay);
    
    document.getElementById('psd-close').addEventListener('click', function() {
      document.getElementById('psd-overlay').style.display = 'none';
    });
    
    log('Overlay creado');
  }

  function updateOverlay(state) {
    const statusEl = document.getElementById('psd-status');
    const debugEl = document.getElementById('psd-debug');
    
    if (!statusEl || !debugEl) return;

    // Información de debug
    let debugHtml = 'Scans: ' + (state.scanCount || 0);
    if (state.urlInfo) {
      debugHtml += '<br>URL: ' + state.urlInfo.pathname;
      debugHtml += '<br>Batalla: ' + (state.urlInfo.isBattleRoom ? '✓' : '✗');
    }
    if (state.domInfo) {
      debugHtml += '<br>.battle: ' + state.domInfo.battle;
      debugHtml += '<br>.left: ' + state.domInfo.left;
      debugHtml += '<br>.right: ' + state.domInfo.right;
    }
    debugEl.innerHTML = debugHtml;

    // Estado principal
    if (!state || !state.hasBattle) {
      statusEl.innerHTML = '<div style="text-align:center;color:#888;">🎮 Esperando batalla...</div>';
      return;
    }

    let html = '';
    
    if (state.myPokemon) {
      html += '<div style="margin-bottom:8px;padding:8px;background:rgba(0,212,255,0.1);border-radius:8px;">';
      html += '<strong style="color:#00d4ff;">⬆️ Tu Pokemon:</strong><br>';
      html += '<span style="font-size:14px;">' + state.myPokemon.name + '</span><br>';
      html += '<span style="font-size:12px;color:' + (state.myPokemon.hpPercent > 50 ? '#00b894' : state.myPokemon.hpPercent > 25 ? '#f39c12' : '#e74c3c') + ';">';
      html += 'HP: ' + state.myPokemon.hpPercent + '%</span>';
      html += '</div>';
    }
    
    if (state.enemyPokemon) {
      html += '<div style="margin-bottom:8px;padding:8px;background:rgba(231,76,60,0.1);border-radius:8px;">';
      html += '<strong style="color:#e74c3c;">⬇️ Enemigo:</strong><br>';
      html += '<span style="font-size:14px;">' + state.enemyPokemon.name + '</span><br>';
      html += '<span style="font-size:12px;color:' + (state.enemyPokemon.hpPercent > 50 ? '#00b894' : state.enemyPokemon.hpPercent > 25 ? '#f39c12' : '#e74c3c') + ';">';
      html += 'HP: ' + state.enemyPokemon.hpPercent + '%</span>';
      html += '</div>';
    }
    
    if (state.turn > 0) {
      html += '<div style="text-align:center;margin-top:8px;padding:4px;background:rgba(255,255,255,0.1);border-radius:4px;font-size:11px;">Turno: ' + state.turn + '</div>';
    }
    
    if (!state.myPokemon && !state.enemyPokemon) {
      html = '<div style="text-align:center;color:#f39c12;">⚠️ Batalla detectada pero Pokemon no identificado</div>';
    }
    
    statusEl.innerHTML = html;
    currentBattleState = state;
  }

  // ==================== INICIALIZACIÓN ====================
  function init() {
    if (isInitialized) return;
    isInitialized = true;

    log('========================================');
    log('INICIANDO PSD ASSISTANT');
    log('========================================');
    log('URL completa:', window.location.href);
    log('pathname:', window.location.pathname);
    log('readyState:', document.readyState);

    createOverlay();
    
    // Configurar observers
    setupHistoryListener();
    setupMutationObserver();
    
    // Scan inicial
    const initialState = scanBattle();
    updateOverlay(initialState);
    
    // Scan periódico
    setInterval(function() {
      // Solo hacer scan si la URL cambió o cada 30 segundos
      if (window.location.href !== lastUrl) {
        lastUrl = window.location.href;
        const state = scanBattle();
        updateOverlay(state);
      }
    }, CONFIG.scanInterval);
    
    log('========================================');
    log('PSD ASSISTANT INICIADO');
    log('========================================');
  }

  // ==================== MENSAJES DEL POPUP ====================
  if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.onMessage) {
    chrome.runtime.onMessage.addListener(function(message, sender, sendResponse) {
      log('Mensaje recibido:', message && message.type ? message.type : 'unknown');

      if (message && message.type === 'TOGGLE_OVERLAY') {
        const el = document.getElementById('psd-overlay');
        if (el) {
          el.style.display = el.style.display === 'none' ? 'block' : 'none';
        }
        sendResponse({ success: true });
      } else if (message && message.type === 'GET_OVERLAY_STATE') {
        sendResponse({ visible: true });
      } else if (message && message.type === 'GET_BATTLE_STATE') {
        sendResponse({ state: currentBattleState });
      } else {
        sendResponse({ success: false });
      }
      return true;
    });
  }

  // Iniciar cuando el DOM esté listo
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

