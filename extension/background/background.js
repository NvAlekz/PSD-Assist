/**
 * Pokemon Showdown Assistant - Background Service Worker
 * Maneja la comunicación entre content scripts y popup
 */

class BackgroundService {
  constructor() {
    this.battleStates = new Map();
    this.setupListeners();
    console.log('[PSD] Background Service initialized');
  }

  setupListeners() {
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      try {
        this.handleMessage(message, sender, sendResponse);
      } catch (error) {
        console.error('[PSD] Error in message handler:', error);
        sendResponse({ success: false, error: error.message });
      }
      return true;
    });
  }

  handleMessage(message, sender, sendResponse) {
    // Verificar que sender.tab existe antes de acceder
    const tabId = sender && sender.tab ? sender.tab.id : null;
    const messageType = message && message.type ? message.type : 'unknown';
    
    console.log('[PSD] Message received:', messageType, 'tabId:', tabId);
    
    if (messageType === 'unknown') {
      sendResponse({ success: false, error: 'Invalid message' });
      return;
    }
    
    switch (messageType) {
      case 'BATTLE_STATE_UPDATE':
        if (tabId && message.data) {
          this.updateBattleState(tabId, message.data);
        }
        sendResponse({ success: true });
        break;
      case 'GET_BATTLE_STATE':
        sendResponse(tabId ? this.getBattleState(tabId) : null);
        break;
      case 'CLEAR_BATTLE':
        if (tabId) {
          this.clearBattle(tabId);
        }
        sendResponse({ success: true });
        break;
      case 'GET_BATTLE_HISTORY':
        sendResponse({ history: this.getBattleHistory(tabId) });
        break;
      case 'TOGGLE_OVERLAY':
        this.notifyContentScript(tabId, { type: 'TOGGLE_OVERLAY' });
        sendResponse({ success: true });
        break;
      default:
        console.log('[PSD] Unknown message type:', messageType);
        sendResponse({ error: 'Unknown message type' });
    }
  }

  updateBattleState(tabId, state) {
    console.log('[PSD] Updating battle state for tab:', tabId);
    this.battleStates.set(tabId, state);
    this.notifyPopup(tabId);
  }

  getBattleState(tabId) {
    return this.battleStates.get(tabId) || null;
  }

  getBattleHistory(tabId) {
    const state = this.battleStates.get(tabId);
    return state ? state.recentActions || [] : [];
  }

  clearBattle(tabId) {
    this.battleStates.delete(tabId);
  }

  notifyPopup(tabId) {
    chrome.runtime.sendMessage({
      type: 'STATE_UPDATED',
      tabId: tabId
    }).catch(err => {
      console.log('[PSD] Popup notification failed:', err.message);
    });
  }
  
  notifyContentScript(tabId, message) {
    if (tabId) {
      chrome.tabs.sendMessage(tabId, message).catch(err => {
        console.log('[PSD] Content script notification failed:', err.message);
      });
    }
  }
}

new BackgroundService();