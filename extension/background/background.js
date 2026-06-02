/**
 * Pokemon Showdown Assistant - Background Service Worker
 * Maneja la comunicación entre content scripts y popup
 */

class BackgroundService {
  constructor() {
    this.battleStates = new Map();
    this.setupListeners();
  }

  setupListeners() {
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      this.handleMessage(message, sender, sendResponse);
      return true;
    });
  }

  handleMessage(message, sender, sendResponse) {
    switch (message.type) {
      case 'BATTLE_STATE_UPDATE':
        this.updateBattleState(sender.tab.id, message.data);
        sendResponse({ success: true });
        break;
      case 'GET_BATTLE_STATE':
        sendResponse(this.getBattleState(sender.tab.id));
        break;
      case 'CLEAR_BATTLE':
        this.clearBattle(sender.tab.id);
        sendResponse({ success: true });
        break;
      default:
        sendResponse({ error: 'Unknown message type' });
    }
  }

  updateBattleState(tabId, state) {
    this.battleStates.set(tabId, state);
    this.notifyPopup(tabId);
  }

  getBattleState(tabId) {
    return this.battleStates.get(tabId) || null;
  }

  clearBattle(tabId) {
    this.battleStates.delete(tabId);
  }

  notifyPopup(tabId) {
    chrome.runtime.sendMessage({
      type: 'STATE_UPDATED',
      tabId: tabId
    }).catch(() => {});
  }
}

new BackgroundService();