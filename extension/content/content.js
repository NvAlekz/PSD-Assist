/**
 * Pokemon Showdown Assistant - Content Script
 * Lee directamente del DOM de Pokemon Showdown y muestra overlay
 */

(function() {
  'use strict';

  // ==================== CONFIGURACIÓN ====================
  const CONFIG = {
    debug: true,
    showNotifications: true
  };

  // ==================== ESTADO ====================
  let overlayVisible = true;
  let isInitialized = false;
  let currentBattleState = null;

  // ==================== UTILIDADES ====================
  function log(message, data) {
    if (CONFIG.debug) {
      console.log('[PSD] ' + message, data || '');
    }
  }

  // ==================== DETECCIÓN DE BATALLA ====================
  function scanBattle() {
    const state = {
      hasBattle: false,
      myPokemon: null,
      enemyPokemon: null,
      turn: 0,
      detected: false,
      isInBattleFrame: false
    };

    const url = window.location.href;

    // Detectar si estamos dentro del iframe de batalla
    if (url.includes('battle-')) {
      state.isInBattleFrame = true;
      log('Estamos en el frame de batalla!');

      const battle = document.querySelector('.battle');
      if (!battle) {
        log('No se encontró .battle en el DOM');
        return state;
      }

      const leftSide = battle.querySelector('.left');
      const rightSide = battle.querySelector('.right');

      if (leftSide) {
        state.myPokemon = extractPokemon(leftSide);
        log('Pokemon mío:', state.myPokemon);
      }

      if (rightSide) {
        state.enemyPokemon = extractPokemon(rightSide);
        log('Pokemon enemigo:', state.enemyPokemon);
      }

      state.hasBattle = true;
      state.detected = !!(state.myPokemon || state.enemyPokemon);
    } else {
      // Estamos en el frame principal - buscar iframes de batalla
      log('Estamos en el frame principal');
      const iframes = document.querySelectorAll('iframe');
      log('Total iframes: ' + iframes.length);

      for (let i = 0; i < iframes.length; i++) {
        const iframe = iframes[i];
        log('Iframe src: ' + iframe.src);
        if (iframe.src && iframe.src.includes('battle-')) {
          state.hasBattle = true;
          state.isInBattleFrame = true;
        }
      }
    }

    return state;
  }

  function extractPokemon(element) {
    if (!element) return null;

    let name = '';

    // Intentar múltiples selectores para el nombre
    const selectors = ['.name', '.pokename', '[data-name]'];
    for (let i = 0; i < selectors.length; i++) {
      const el = element.querySelector(selectors[i]);
      if (el && el.textContent) {
        name = el.textContent.trim();
        if (name) break;
      }
    }

    // Si no hay nombre, buscar en el sprite
    if (!name) {
      const sprite = element.querySelector('.sprite, .pokemonicon, img');
      if (sprite) {
        name = sprite.getAttribute('title') || sprite.getAttribute('alt') || '';
      }
    }

    name = name.replace(/^(Mega|Alola|Galar|Dynamax|Prime|Z)-?\s*/i, '');
    if (!name) return null;

    // HP
    let hp = 100, maxHp = 100;
    const hpBar = element.querySelector('.hpbar, .hptext');
    if (hpBar) {
      const title = hpBar.getAttribute('title') || hpBar.textContent || '';
      const match = title.match(/(\d+)\s*\/\s*(\d+)/);
      if (match) {
        hp = parseInt(match[1]) || 0;
        maxHp = parseInt(match[2]) || hp;
      }
    }

    return {
      name: name,
      species: name.split(' ')[0],
      hp: hp,
      maxHp: maxHp,
      hpPercent: maxHp > 0 ? Math.round((hp / maxHp) * 100) : 100,
      status: null,
      fainted: hp === 0
    };
  }

  // ==================== OVERLAY ====================
  function createOverlay() {
    if (document.getElementById('psd-overlay')) return;

    const overlay = document.createElement('div');
    overlay.id = 'psd-overlay';
    overlay.innerHTML = '<div style="padding:20px;background:#1a1a2e;color:#fff;font-family:Segoe UI,sans-serif;">' +
      '<h3 style="margin:0 0 10px 0;color:#00d4ff;">⚡ PSD Assistant</h3>' +
      '<div id="psd-status">Iniciando...</div>' +
      '<button onclick="document.getElementById(\'psd-overlay\').style.display=\'none\'" style="margin-top:10px;padding:5px 10px;cursor:pointer;">Cerrar</button>' +
      '</div>';
    document.body.appendChild(overlay);
    log('Overlay creado');
  }

  function updateOverlay(state) {
    const statusEl = document.getElementById('psd-status');
    if (!statusEl) return;

    if (!state || !state.hasBattle) {
      statusEl.innerHTML = '🎮 Esperando batalla...';
      return;
    }

    let html = '';
    if (state.myPokemon) {
      html += '<div style="margin-bottom:10px;">Tu Pokemon: <strong>' + state.myPokemon.name + '</strong> (' + state.myPokemon.hpPercent + '% HP)</div>';
    }
    if (state.enemyPokemon) {
      html += '<div style="margin-bottom:10px;">Enemigo: <strong>' + state.enemyPokemon.name + '</strong> (' + state.enemyPokemon.hpPercent + '% HP)</div>';
    }
    if (!state.myPokemon && !state.enemyPokemon) {
      html = 'Batalla detectada pero Pokemon no identificado';
    }

    statusEl.innerHTML = html;
    currentBattleState = state;
  }

  // ==================== MENSAJES ====================
  window.addEventListener('message', function(event) {
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
    log('URL: ' + window.location.href);

    createOverlay();
    scanBattle();
    updateOverlay(scanBattle());
    setInterval(function() {
      const state = scanBattle();
      updateOverlay(state);
    }, 1000);

    log('Extension iniciada correctamente');
  }

  // Chrome runtime messages
  if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.onMessage) {
    chrome.runtime.onMessage.addListener(function(message, sender, sendResponse) {
      log('Mensaje recibido: ' + (message && message.type ? message.type : 'unknown'));

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

  init();
})();

