/**
 * Pokemon Showdown Assistant - Popup Script
 */

let battleCount = 0;
let overlayState = 'unknown';

document.addEventListener('DOMContentLoaded', () => {
  loadState();
  setupListeners();
  checkOverlayState();
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
    if (state && state.myPokemon) {
      statusEl.className = 'status active';
      statusEl.textContent = '⚔️ Batalla activa';
    } else {
      statusEl.className = 'status inactive';
      statusEl.textContent = 'Sin batalla activa';
    }
  });
}

function updateBattleCount() {
  document.getElementById('battle-count').textContent = `Batallas: ${battleCount}`;
}

function checkOverlayState() {
  // Query active tab and check overlay state
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]) {
      chrome.tabs.sendMessage(tabs[0].id, { type: 'GET_OVERLAY_STATE' }, (response) => {
        const statusEl = document.getElementById('toggle-status');
        if (response && response.visible) {
          statusEl.textContent = 'Estado: Visible ✓';
          overlayState = 'visible';
        } else {
          statusEl.textContent = 'Estado: Oculto';
          overlayState = 'hidden';
        }
      }).catch(() => {
        document.getElementById('toggle-status').textContent = 'Estado: No disponible';
      });
    }
  });
}

function toggleOverlayState() {
  // Send message directly to content script via tabs API
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]) {
      chrome.tabs.sendMessage(tabs[0].id, { type: 'TOGGLE_OVERLAY' }, (response) => {
        const statusEl = document.getElementById('toggle-status');
        if (response && response.success) {
          // Toggle the text based on current state
          if (overlayState === 'visible') {
            statusEl.textContent = 'Estado: Oculto';
            overlayState = 'hidden';
          } else {
            statusEl.textContent = 'Estado: Visible ✓';
            overlayState = 'visible';
          }
        }
      }).catch((error) => {
        console.error('[PSD] Error toggling overlay:', error);
        document.getElementById('toggle-status').textContent = 'Error: Extensión no detectada';
      });
    }
  });
}

function setupListeners() {
  document.getElementById('toggleOverlay').addEventListener('click', toggleOverlayState);
  
  document.getElementById('clearData').addEventListener('click', () => {
    chrome.storage.local.clear();
    battleCount = 0;
    updateBattleCount();
    updateBattleStatus();
  });
  
  chrome.runtime.onMessage.addListener((message) => {
    if (message.type === 'STATE_UPDATED') {
      updateBattleStatus();
      battleCount++;
      chrome.storage.local.set({ battleCount });
      updateBattleCount();
    }
  });
}