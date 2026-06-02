/**
 * Pokemon Showdown Assistant - Popup Script
 */

let battleCount = 0;

document.addEventListener('DOMContentLoaded', () => {
  loadState();
  setupListeners();
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

function setupListeners() {
  document.getElementById('toggleOverlay').addEventListener('click', () => {
    chrome.runtime.sendMessage({ type: 'TOGGLE_OVERLAY' });
  });
  
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