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
    return scanBattleImproved();
  }

  // ==================== EXTRAER POKEMON ====================
  function extractPokemon(element) {
    if (!element) return null;

    log('Extrayendo Pokemon de elemento...');

    // Intentar múltiples selectores para el nombre
    let name = '';
    
    // Selectores de nombre (ordenados por probabilidad)
    const nameSelectors = [
      '.nickname',           // Pokemon nickname
      '.pokename',           // Pokemon name
      '.name',               // Generic name
      '.pokemon-name',       // Pokemon name class
      '.trainer-name',       // Trainer name
      '[data-name]',         // Data attribute
      '[data-nickname]',     // Nickname data
      '.foename',            // Foe name
      '.username',           // Username (enemy)
    ];
    
    for (let i = 0; i < nameSelectors.length; i++) {
      const selector = nameSelectors[i];
      const el = element.querySelector(selector);
      if (el && el.textContent) {
        const text = el.textContent.trim();
        log('  Selector ' + selector + ' encontró:', text);
        if (text && text.length > 0 && text.length < 30) {
          name = text;
          break;
        }
      }
    }

    // Si no hay nombre, buscar en el sprite
    if (!name) {
      const spriteSelectors = ['.sprite', '.pokemonicon', '.pokemonsprite', '.pokemon-sprite', 'img'];
      for (let i = 0; i < spriteSelectors.length; i++) {
        const sprite = element.querySelector(spriteSelectors[i]);
        if (sprite) {
          name = sprite.getAttribute('title') || sprite.getAttribute('alt') || '';
          log('  Sprite ' + spriteSelectors[i] + ' title/alt:', name);
          if (name) break;
        }
      }
    }

    // Limpiar nombre
    name = name.replace(/^(Mega|Alola|Galar|Dynamax|Prime|Z)-?\s*/i, '');
    name = name.split(' ')[0]; // Solo el nombre base
    name = name.split('-')[0]; // Remover formas como Hisui
    
    if (!name || name.length === 0) {
      log('  ✗ No se pudo extraer nombre');
      return null;
    }

    log('  Nombre extraído:', name);

    // HP - múltiples formas
    let hp = 100, maxHp = 100;
    
    // Intentar diferentes selectores de HP
    const hpSelectors = [
      '.statbar-lifeline',
      '.hpbar',
      '.hp-text',
      '.hptext',
      '.hpnumber',
      '[class*="hp-bar"]',
      '[class*="hpbar"]',
      '[class*="lifeline"]'
    ];
    
    for (let i = 0; i < hpSelectors.length; i++) {
      const hpEl = element.querySelector(hpSelectors[i]);
      if (hpEl) {
        const title = hpEl.getAttribute('title') || '';
        const text = hpEl.textContent || '';
        const dataHp = hpEl.getAttribute('data-hp') || '';
        const hpSource = title || text || dataHp;
        log('  HP selector ' + hpSelectors[i] + ':', hpSource);
        
        if (hpSource) {
          // Formato: "100/100" o "100 / 100"
          const match = hpSource.match(/(\d+)\s*\/?\s*(\d*)/);
          if (match) {
            hp = parseInt(match[1]) || 0;
            maxHp = parseInt(match[2]) || hp;
            break;
          }
        }
      }
    }

    // Status
    let status = null;
    const statusEl = element.querySelector('.status, [class*="status"]');
    if (statusEl) {
      const statusText = statusEl.textContent || '';
      log('  Status:', statusText);
      if (statusText.includes('brn') || statusText.includes('burn')) status = 'burned';
      else if (statusText.includes('psn')) status = 'poisoned';
      else if (statusText.includes('tox')) status = 'toxic';
      else if (statusText.includes('slp')) status = 'sleep';
      else if (statusText.includes('frz')) status = 'frozen';
      else if (statusText.includes('par')) status = 'paralyzed';
    }

    return {
      name: name,
      hp: hp,
      maxHp: maxHp,
      hpPercent: maxHp > 0 ? Math.round((hp / maxHp) * 100) : 100,
      status: status,
      fainted: hp === 0
    };
  }

  // ==================== EXTRAER POKEMON MEJORADO ====================
  function extractAllPokemonData() {
    log('=== BUSCANDO TODOS LOS POKEMON ===');
    
    const results = {
      myPokemon: null,
      enemyPokemon: null,
      allPokemonFound: []
    };
    
    // Buscar por múltiples métodos
    // Método 1: Buscar por lado (.left, .right, .p1, .p2)
    const sideSelectors = ['.left', '.right', '.side-left', '.side-right', '.p1', '.p2', '.trainer-0', '.trainer-1'];
    for (let i = 0; i < sideSelectors.length; i++) {
      const selector = sideSelectors[i];
      const elements = document.querySelectorAll(selector);
      log('  Selector ' + selector + ': ' + elements.length + ' elementos');
      
      elements.forEach((el, idx) => {
        const nameEl = el.querySelector('.name, .pokename, .nickname, .username');
        if (nameEl) {
          const name = nameEl.textContent.trim();
          log('    ' + selector + '[' + idx + '] nombre:', name);
          results.allPokemonFound.push({
            name: name,
            selector: selector,
            element: el
          });
        }
      });
    }
    
    // Método 2: Buscar statbar (contenedor de HP y nombre)
    const statbarElements = document.querySelectorAll('[class*="statbar"], [class*="lifeline"]');
    log('  statbar elements:', statbarElements.length);
    
    statbarElements.forEach((el, idx) => {
      const nameEl = el.querySelector('.name, .pokename, .nickname');
      const hpEl = el.querySelector('[class*="hp"]');
      if (nameEl) {
        const name = nameEl.textContent.trim();
        log('    statbar[' + idx + '] nombre:', name, 'HP:', hpEl ? hpEl.textContent : 'no hp');
      }
    });
    
    // Método 3: Buscar todos los elementos con 'pokemon' en clase
    const pokemonElements = document.querySelectorAll('[class*="pokemon"]');
    log('  pokemon class elements:', pokemonElements.length);
    
    pokemonElements.forEach((el, idx) => {
      const nameEl = el.querySelector('.name, .pokename, .nickname');
      if (nameEl) {
        const name = nameEl.textContent.trim();
        log('    pokemon[' + idx + '] name:', name, 'class:', el.className);
      }
    });
    
    // Método 4: Buscar por estructura de statrow
    const statrowElements = document.querySelectorAll('.statrow, [class*="statrow"]');
    log('  statrow elements:', statrowElements.length);
    
    // Determinar aliado vs enemigo (heurística)
    // Usually: .left or .p1 = player, .right or .p2 = enemy
    // But we can also check position in DOM or class names
    
    return results;
  }

  // ==================== INSPECCIONAR STATBARS (DEBUG) ====================
  function inspectStatbars() {
    log('=== INSPECCIONANDO TODOS LOS STATBARS ===');
    
    // Buscar todos los elementos que podrían contener HP
    const potentialStatbars = document.querySelectorAll('[class*="statbar"], [class*="lifeline"], .statrow, [class*="HP"], [class*="hp-"]');
    log('Potenciales statbars encontrados:', potentialStatbars.length);
    
    potentialStatbars.forEach((el, idx) => {
      log('');
      log('========== STATBAR ' + idx + ' ==========');
      log('Tag:', el.tagName);
      log('className:', el.className);
      log('id:', el.id);
      log('outerHTML (primeros 300 chars):', el.outerHTML.substring(0, 300));
      log('textContent:', el.textContent.substring(0, 200));
      
      // Buscar todos los elementos hijos con texto
      const childrenWithText = [];
      el.querySelectorAll('*').forEach((child, cIdx) => {
        const text = child.textContent.trim();
        if (text && text.length < 50) {
          childrenWithText.push({
            tag: child.tagName,
            class: child.className,
            text: text,
            idx: cIdx
          });
        }
      });
      
      if (childrenWithText.length > 0) {
        log('Hijos con texto:', JSON.stringify(childrenWithText.slice(0, 10)));
      }
      
      // Buscar atributos
      const attrs = [];
      for (let a = 0; a < el.attributes.length; a++) {
        const attr = el.attributes[a];
        if (attr.name !== 'style') {
          attrs.push(attr.name + '=' + attr.value);
        }
      }
      log('Atributos:', attrs.join(', '));
    });
    
    // Buscar específicamente por elementos que contengan texto de Pokemon
    log('');
    log('=== BUSCANDO TEXTOS DE POKEMON ===');
    
    // Buscar todos los elementos con texto
    const allTextElements = document.querySelectorAll('.nickname, .pokename, .name, [data-nickname], [data-pokemon]');
    allTextElements.forEach((el, idx) => {
      log('  Elemento de nombre[' + idx + ']:', el.tagName, el.className, '"' + el.textContent.trim() + '"');
    });
    
    // Buscar por innerText más específico
    const innerTextElements = document.querySelectorAll('[class*="name"], [class*="pokemon"]');
    log('  Elementos con "name" o "pokemon" en clase:', innerTextElements.length);
    
    innerTextElements.forEach((el, idx) => {
      const text = el.textContent.trim();
      if (text && text.length > 0 && text.length < 40) {
        log('    [' + idx + ']:', el.tagName, el.className, '"' + text + '"');
      }
    });
  }

  // ==================== EXTRAER POKEMON DESDE STATBAR ====================
  function extractPokemonFromStatbar(statbarEl, index) {
    if (!statbarEl) return null;
    
    log('  Extrayendo Pokemon del statbar[' + index + ']...');
    
    let name = '';
    let hp = 100, maxHp = 100;
    let status = null;
    
    // Método 1: Buscar elementos con clase que contenga "name"
    const nameElements = statbarEl.querySelectorAll('[class*="name"], [class*="nick"], [data-name], [data-nickname]');
    log('    Elementos con name/nick:', nameElements.length);
    
    for (let i = 0; i < nameElements.length && !name; i++) {
      const text = nameElements[i].textContent.trim();
      log('    name element[' + i + ']:', text);
      if (text && text.length > 0 && text.length < 30) {
        name = text;
      }
    }
    
    // Método 2: Buscar en data attributes
    if (!name) {
      const dataName = statbarEl.getAttribute('data-name') || 
                      statbarEl.getAttribute('data-nickname') ||
                      statbarEl.getAttribute('data-pokemon');
      if (dataName) {
        log('    data-name:', dataName);
        name = dataName;
      }
    }
    
    // Método 3: Buscar en aria-label
    if (!name) {
      const ariaLabel = statbarEl.getAttribute('aria-label') ||
                        statbarEl.querySelector('[aria-label]')?.getAttribute('aria-label');
      if (ariaLabel) {
        log('    aria-label:', ariaLabel);
        // El aria-label puede contener "PokemonName 100/100"
        const match = ariaLabel.match(/^([A-Za-z0-9-]+)/);
        if (match) {
          name = match[1];
        }
      }
    }
    
    // Método 4: Buscar en title de elementos hijos
    if (!name) {
      const titleEl = statbarEl.querySelector('[title]');
      if (titleEl) {
        const title = titleEl.getAttribute('title');
        log('    title:', title);
        const match = title.match(/^([A-Za-z0-9-]+)/);
        if (match) {
          name = match[1];
        }
      }
    }
    
    // Método 5: Buscar en el primer texto directo del elemento
    if (!name) {
      // El primer nodo de texto hijo
      for (let i = 0; i < statbarEl.childNodes.length; i++) {
        const node = statbarEl.childNodes[i];
        if (node.nodeType === Node.TEXT_NODE) {
          const text = node.textContent.trim();
          if (text && text.length > 0 && text.length < 30) {
            log('    texto directo:', text);
            name = text;
            break;
          }
        }
      }
    }
    
    // Método 6: Extraer nombre del primer hijo con clase que no sea hpbar o statbar
    if (!name) {
      const children = statbarEl.children;
      for (let i = 0; i < children.length && !name; i++) {
        const child = children[i];
        const className = child.className || '';
        if (!className.includes('hp') && !className.includes('stat') && !className.includes('bar')) {
          const text = child.textContent.trim();
          if (text && text.length > 0 && text.length < 30) {
            log('    hijo[' + i + '] (sin hp/stat):', className, '"' + text + '"');
            name = text;
          }
        }
      }
    }
    
    // Limpiar nombre
    name = name.replace(/^(Mega|Alola|Galar|Dynamax|Prime|Z)-?\s*/i, '');
    name = name.split('-')[0]; // Remover formas como Hisui
    
    if (!name) {
      log('    ✗ No se pudo extraer nombre');
      return null;
    }
    
    log('    ✓ Nombre extraído:', name);
    
    // Extraer HP
    const hpMatches = statbarEl.textContent.match(/(\d+)\s*\/?\s*(\d*)/g);
    if (hpMatches && hpMatches.length > 0) {
      // Tomar el primer match que parece HP
      for (let i = 0; i < hpMatches.length; i++) {
        const match = hpMatches[i].match(/(\d+)\s*\/?\s*(\d*)/);
        if (match) {
          hp = parseInt(match[1]) || 0;
          maxHp = parseInt(match[2]) || hp;
          if (maxHp > hp) { // Solo si tenemos dos números (HP actual y max)
            break;
          }
        }
      }
    }
    
    log('    HP:', hp + '/' + maxHp);
    
    // Detectar status
    const statusText = statbarEl.textContent.toLowerCase();
    if (statusText.includes('brn')) status = 'burned';
    else if (statusText.includes('psn')) status = 'poisoned';
    else if (statusText.includes('tox')) status = 'toxic';
    else if (statusText.includes('slp')) status = 'sleep';
    else if (statusText.includes('frz')) status = 'frozen';
    else if (statusText.includes('par')) status = 'paralyzed';
    
    return {
      name: name,
      hp: hp,
      maxHp: maxHp,
      hpPercent: maxHp > 0 ? Math.round((hp / maxHp) * 100) : 100,
      status: status,
      fainted: hp === 0
    };
  }

  // ==================== SCAN DE BATALLA MEJORADO ====================
  function scanBattleImproved() {
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

    log('=== SCAN #' + scanCount + ' ===');
    log('URL:', window.location.href);

    // Si estamos en un frame de batalla
    if (urlInfo.isBattleRoom) {
      log('=== MODO BATALLA (URL) ===');
      
      // Ejecutar inspección de statbars para debug
      inspectStatbars();
      
      // Buscar el contenedor de batalla
      const battle = document.querySelector('.battle');
      
      if (!battle) {
        log('⚠️ No se encontró .battle');
        // Intentar otros contenedores
        const alternatives = ['#battle', '.battle-arena', '.battle-wrapper', '[id*="battle"]'];
        for (let i = 0; i < alternatives.length; i++) {
          const alt = document.querySelector(alternatives[i]);
          if (alt) {
            log('✓ Encontré alternativa: ' + alternatives[i]);
            return scanBattleInElement(alt, state);
          }
        }
        return state;
      }
      
      return scanBattleInElement(battle, state);
    }
    
    // Buscar battle en el DOM aunque no estemos en URL de batalla
    log('=== BUSCANDO BATALLA EN DOM ===');
    
    // Buscar directamente por la clase battle
    const battleElements = document.querySelectorAll('.battle, [class*="battle-aren"]');
    log('Elementos .battle:', battleElements.length);
    
    if (battleElements.length > 0) {
      log('✓ Encontré elementos .battle!');
      
      // Ejecutar inspección de statbars para debug
      inspectStatbars();
      
      return scanBattleInElement(battleElements[0], state);
    }
    
    // Extraer todos los datos de Pokemon para debug
    const pokemonData = extractAllPokemonData();
    log('Pokemon encontrados:', pokemonData.allPokemonFound);
    
    // Si encontramos pokemon data, intentar determinar aliado/enemigo
    if (pokemonData.allPokemonFound.length > 0) {
      // Asumir que los primeros son aliados y los últimos enemigos
      // Esto es una heurística
      log('Total pokemon encontrados:', pokemonData.allPokemonFound.length);
    }
    
    return state;
  }
  
  function scanBattleInElement(element, state) {
    if (!element) return state;
    
    log('Escaneando elemento:', element.className);
    state.hasBattle = true;
    
    // Ejecutar inspección completa de statbars
    inspectStatbars();
    
    // MÉTODO PRINCIPAL: Usar extractPokemonFromStatbar para cada statbar
    log('');
    log('=== USANDO EXTRACTPOKEMONFROMSTATBAR ===');
    
    const statbarElements = element.querySelectorAll('[class*="statbar"], [class*="lifeline"]');
    log('Statbars encontrados en elemento:', statbarElements.length);
    
    let statbarIndex = 0;
    statbarElements.forEach((statbar, idx) => {
      log('');
      log('--- Procesando statbar[' + idx + '] ---');
      const pokemon = extractPokemonFromStatbar(statbar, idx);
      
      if (pokemon && pokemon.name) {
        log('✓ Pokemon extraído:', pokemon.name, pokemon.hpPercent + '%');
        
        // Asignar como aliado o enemigo según posición
        if (idx % 2 === 0) {
          if (!state.myPokemon) {
            state.myPokemon = pokemon;
            log('  → Asignado como MI pokemon');
          }
        } else {
          if (!state.enemyPokemon) {
            state.enemyPokemon = pokemon;
            log('  → Asignado como ENEMIGO');
          }
        }
      }
    });
    
    // MÉTODO ALTERNATIVO: Buscar por estructura clásica .left .right
    if (!state.myPokemon || !state.enemyPokemon) {
      log('');
      log('=== MÉTODO ALTERNATIVO: .left .right ===');
      log('  Buscando .left y .right...');
      const leftSide = element.querySelector('.left, .side-left, .p1, .trainer-0, [class*="side-left"]');
      const rightSide = element.querySelector('.right, .side-right, .p2, .trainer-1, [class*="side-right"]');
      
      if (leftSide) {
        log('  ✓ .left encontrado:', leftSide.className);
        const pokemon = extractPokemonFromStatbar(leftSide, -1);
        if (pokemon && !state.myPokemon) {
          state.myPokemon = pokemon;
          log('  ✓ Pokemon mío extraído:', state.myPokemon.name, state.myPokemon.hpPercent + '%');
        }
      }
      
      if (rightSide) {
        log('  ✓ .right encontrado:', rightSide.className);
        const pokemon = extractPokemonFromStatbar(rightSide, -2);
        if (pokemon && !state.enemyPokemon) {
          state.enemyPokemon = pokemon;
          log('  ✓ Pokemon enemigo extraído:', state.enemyPokemon.name, state.enemyPokemon.hpPercent + '%');
        }
      }
    }
    
    // MÉTODO 3: Buscar por todos los elementos con nombre
    if (!state.myPokemon) {
      log('');
      log('=== MÉTODO 3: Buscar por nombre directamente ===');
      const allNameElements = element.querySelectorAll('[class*="name"], [class*="nick"]');
      log('  Elementos con name/nick:', allNameElements.length);
      
      allNameElements.forEach((el, idx) => {
        const text = el.textContent.trim();
        if (text && text.length > 0 && text.length < 30 && !text.includes(' ')) {
          log('    [' + idx + ']:', el.tagName, el.className, '"' + text + '"');
          
          if (!state.myPokemon && idx < allNameElements.length / 2) {
            const parent = el.closest('[class*="statbar"], [class*="lifeline"], .left, .side, [class*="pokemon"]');
            if (parent) {
              state.myPokemon = extractPokemonFromStatbar(parent, -3);
              log('    → MI pokemon:', state.myPokemon ? state.myPokemon.name : 'null');
            }
          } else if (!state.enemyPokemon && idx >= allNameElements.length / 2) {
            const parent = el.closest('[class*="statbar"], [class*="lifeline"], .right, .side, [class*="pokemon"]');
            if (parent) {
              state.enemyPokemon = extractPokemonFromStatbar(parent, -4);
              log('    → ENEMIGO:', state.enemyPokemon ? state.enemyPokemon.name : 'null');
            }
          }
        }
      });
    }
    
    // Buscar turno
    const turnEl = element.querySelector('.turn-count, [class*="turn"]');
    if (turnEl) {
      state.turn = parseInt(turnEl.textContent) || 0;
      log('  Turno:', state.turn);
    }
    
    state.detected = !!(state.myPokemon || state.enemyPokemon);
    log('');
    log('=== RESULTADO FINAL ===');
    log('  MI pokemon:', state.myPokemon);
    log('  ENEMIGO:', state.enemyPokemon);
    log('  Detectado:', state.detected);
    
    return state;
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

