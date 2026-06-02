/**
 * Pokemon Showdown Assistant - Content Script
 * Lee directamente del DOM de Pokemon Showdown
 */

class ShowdownParser {
  constructor() {
    this.battleLog = [];
    this.battleHistory = [];
    this.init();
  }

  init() {
    this.observer = new MutationObserver(() => this.scanBattle());
    this.scanBattle();
    this.observer.observe(document.body, { childList: true, subtree: true });
  }

  /**
   * Escanea el estado actual de la batalla
   */
  scanBattle() {
    const state = this.extractBattleState();
    if (state) {
      chrome.runtime.sendMessage({
        type: 'BATTLE_STATE_UPDATE',
        data: {
          ...state,
          recentActions: this.battleHistory.slice(-5)
        }
      });
    }
  }

  /**
   * Extrae el estado de la batalla del DOM
   */
  extractBattleState() {
    const myActive = this.getActivePokemon('left');
    const enemyActive = this.getActivePokemon('right');
    
    if (!myActive && !enemyActive) {
      return null;
    }

    // Agregar al historial si cambió el Pokemon activo
    if (myActive && this.lastMyPokemon !== myActive.name) {
      this.addHistoryEvent('switch', `${myActive.name} entró`);
      this.lastMyPokemon = myActive.name;
    }
    if (enemyActive && this.lastEnemyPokemon !== enemyActive.name) {
      this.addHistoryEvent('switch', `Enemigo envió a ${enemyActive.name}`);
      this.lastEnemyPokemon = enemyActive.name;
    }

    return {
      timestamp: Date.now(),
      myPokemon: myActive,
      enemyPokemon: enemyActive,
      myTeam: this.getTeam('left'),
      enemyTeam: this.getTeam('right'),
      availableMoves: this.getAvailableMoves(),
      availableSwitches: this.getAvailableSwitches(),
      hazards: this.extractHazards()
    };
  }

  addHistoryEvent(type, description, data = {}) {
    this.battleHistory.push({
      type,
      description,
      timestamp: Date.now(),
      ...data
    });
    
    // Mantener solo últimos 50 eventos
    if (this.battleHistory.length > 50) {
      this.battleHistory.shift();
    }
  }

  /**
   * Obtiene el Pokemon activo
   * @param {string} side - 'left' o 'right'
   */
  getActivePokemon(side) {
    const selector = `.battle-sidebar .${side} .pokeball`;
    const elements = document.querySelectorAll(selector);
    
    for (const el of elements) {
      const activeIndicator = el.closest('.pokemon').querySelector('.active');
      if (activeIndicator) {
        return this.parsePokemonElement(el.closest('.pokemon'));
      }
    }
    return null;
  }

  /**
   * Obtiene el equipo de un lado
   * @param {string} side - 'left' o 'right'
   */
  getTeam(side) {
    const team = [];
    const pokemonElements = document.querySelectorAll(`.battle-sidebar .${side} .pokemon`);
    
    pokemonElements.forEach(el => {
      team.push(this.parsePokemonElement(el));
    });
    
    return team;
  }

  /**
   * Parsea un elemento Pokemon del DOM
   * @param {HTMLElement} element
   */
  parsePokemonElement(element) {
    const nameEl = element.querySelector('.name');
    const hpBarEl = element.querySelector('.hpbar');
    const statusEl = element.querySelector('.status');
    
    const name = nameEl ? nameEl.textContent.trim() : 'Unknown';
    const hpText = hpBarEl ? hpBarEl.dataset.hp : '100/100';
    const [current, max] = hpText.split('/').map(Number);
    const status = statusEl ? statusEl.textContent.trim() : null;
    
    return {
      name: name.replace(/^[^a-zA-Z]+/, ''),
      species: name.split(' ')[0],
      hp: current,
      maxHp: max,
      hpPercent: max > 0 ? Math.round((current / max) * 100) : 100,
      status: this.parseStatus(status),
      fainted: current === 0
    };
  }

  /**
   * Parsea el estado del Pokemon
   * @param {string} statusText
   */
  parseStatus(statusText) {
    if (!statusText) return null;
    
    const statusMap = {
      'brn': 'burned',
      'psn': 'poisoned',
      'tox': 'toxic',
      'slp': 'sleep',
      'frz': 'frozen',
      'par': 'paralyzed',
      'confusion': 'confused'
    };
    
    return statusMap[statusText.toLowerCase()] || null;
  }

  /**
   * Obtiene movimientos disponibles
   */
  getAvailableMoves() {
    const moves = [];
    const moveElements = document.querySelectorAll('.movemenu .move');
    
    moveElements.forEach(el => {
      const name = el.querySelector('.movename')?.textContent;
      const pp = el.querySelector('.pp')?.textContent;
      if (name) {
        moves.push({
          name: name.trim(),
          pp: pp || '?/?'
        });
      }
    });
    
    return moves;
  }

  /**
   * Obtiene cambios disponibles
   */
  getAvailableSwitches() {
    const switches = [];
    const switchElements = document.querySelectorAll('.switchmenu .switch');
    
    switchElements.forEach(el => {
      const name = el.querySelector('.pokemonname')?.textContent;
      const hp = el.querySelector('.hp')?.textContent;
      if (name) {
        switches.push({
          name: name.trim(),
          hp: hp || '100%'
        });
      }
    });
    
    return switches;
  }

  /**
   * Extrae hazards del campo
   */
  extractHazards() {
    return {
      spikes: document.querySelector('.spikes') ? this.countHazards('.spikes') : 0,
      toxicSpikes: document.querySelector('.toxicspikes') ? this.countHazards('.toxicspikes') : 0,
      stealthRock: !!document.querySelector('.stealthrock'),
      stickyWeb: !!document.querySelector('.stickyweb')
    };
  }

  countHazards(selector) {
    const element = document.querySelector(selector);
    return element ? element.textContent.split('').length : 0;
  }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
  new ShowdownParser();
});