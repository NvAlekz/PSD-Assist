/**
 * Pokemon Showdown Assistant - Popup Script
 */

let battleCount = 0;
let overlayState = 'unknown';

document.addEventListener('DOMContentLoaded', () => {
  loadState();
  setupListeners();
  // Delay check to ensure content script is loaded
  setTimeout(checkOverlayState, 500);
});

function loadState() {
  chrome.storage.local.get(['battleCount'], (result) => {
    battleCount = result.battleCount || 0;
    updateBattleCount();
  });
  
  updateBattleStatus();
}

function updateBattleStatus() {
  chrome.runtime.sendMessage({ type: 'GET_BATTLE_STATE' }, (state) => {
    const statusEl = document.getElementById('status');
    if (statusEl) {
      if (state && state.myPokemon) {
        statusEl.className = 'status active';
        statusEl.textContent = '⚔️ Batalla activa';
      } else {
        statusEl.className = 'status inactive';
        statusEl.textContent = 'Sin batalla activa';
      }
    }
  });
}

function updateBattleCount() {
  const el = document.getElementById('battle-count');
  if (el) el.textContent = `Batallas: ${battleCount}`;
}

function checkOverlayState() {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (!tabs || !tabs[0]) {
      updateToggleStatus('Estado: Sin pestaña activa');
      return;
    }
    
    try {
      chrome.tabs.sendMessage(tabs[0].id, { type: 'GET_OVERLAY_STATE' }, (response) => {
        if (chrome.runtime.lastError) {
          updateToggleStatus('Estado: Extensión no detectada');
          console.log('[PSD] Runtime error:', chrome.runtime.lastError.message);
        } else if (response && response.visible !== undefined) {
          if (response.visible) {
            updateToggleStatus('Estado: Visible ✓');
            overlayState = 'visible';
          } else {
            updateToggleStatus('Estado: Oculto');
            overlayState = 'hidden';
          }
        } else {
          updateToggleStatus('Estado: Respuesta inválida');
        }
      });
    } catch (e) {
      updateToggleStatus('Estado: Error de conexión');
      console.error('[PSD] Error:', e);
    }
  });
}

function toggleOverlayState() {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (!tabs || !tabs[0]) {
      updateToggleStatus('Estado: Sin pestaña activa');
      return;
    }
    
    try {
      chrome.tabs.sendMessage(tabs[0].id, { type: 'TOGGLE_OVERLAY' }, (response) => {
        if (chrome.runtime.lastError) {
          updateToggleStatus('Error: ' + chrome.runtime.lastError.message);
          console.log('[PSD] Runtime error:', chrome.runtime.lastError.message);
        } else if (response && response.success) {
          // Toggle state
          if (overlayState === 'visible') {
            updateToggleStatus('Estado: Oculto');
            overlayState = 'hidden';
          } else {
            updateToggleStatus('Estado: Visible ✓');
            overlayState = 'visible';
          }
        } else {
          updateToggleStatus('Estado: Sin respuesta');
        }
      });
    } catch (e) {
      updateToggleStatus('Error: ' + e.message);
      console.error('[PSD] Error toggling:', e);
    }
  });
}

function updateToggleStatus(text) {
  const el = document.getElementById('toggle-status');
  if (el) el.textContent = text;
}

function setupListeners() {
  const toggleBtn = document.getElementById('toggleOverlay');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', toggleOverlayState);
  }
  
  const clearBtn = document.getElementById('clearData');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      chrome.storage.local.clear();
      battleCount = 0;
      updateBattleCount();
      updateBattleStatus();
    });
  }
  
  chrome.runtime.onMessage.addListener((message) => {
    if (message.type === 'STATE_UPDATED') {
      updateBattleStatus();
      battleCount++;
      chrome.storage.local.set({ battleCount });
      updateBattleCount();
    }
  });
}