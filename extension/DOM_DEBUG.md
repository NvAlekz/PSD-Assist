# DOM Debug - Pokemon Showdown Battle

Este documento sirve para registrar los selectores y elementos encontrados durante una batalla real.

## Cómo usar este documento

1. Abre Pokemon Showdown en una batalla
2. Abre DevTools (F12) → Console
3. Copia y ejecuta los comandos de abajo para explorar el DOM

---

## Comandos de exploración

### 1. Ver estructura del battle container

```javascript
// Ver todos los elementos con 'battle' en la clase
document.querySelectorAll('[class*="battle"]').forEach((el, i) => {
  console.log(i + ':', el.tagName, el.className, el.id);
});

// Ver el primer .battle y sus hijos directos
const battle = document.querySelector('.battle');
if (battle) {
  console.log('Battle element:', battle.tagName, battle.className);
  console.log('Children:', battle.children.length);
  Array.from(battle.children).forEach((child, i) => {
    console.log('  ' + i + ':', child.tagName, child.className);
  });
}
```

### 2. Ver todas las clases únicas

```javascript
// Listar todas las clases únicas en el documento
const classes = new Set();
document.querySelectorAll('[class]').forEach(el => {
  el.classList.forEach(c => classes.add(c));
});
console.log('Todas las clases:', [...classes].join('\n'));
```

### 3. Ver elementos statbar (donde está el HP)

```javascript
document.querySelectorAll('[class*="statbar"], [class*="hp"]').forEach((el, i) => {
  console.log(i + ':', el.tagName, el.className, 'text:', el.textContent.substring(0, 100));
});
```

### 4. Ver elementos con nombre de Pokemon

```javascript
document.querySelectorAll('.name, [class*="name"], [data-name]').forEach((el, i) => {
  console.log(i + ':', el.tagName, el.className, 'text:', el.textContent.trim());
});
```

### 5. Ver sprites

```javascript
document.querySelectorAll('img[class*="sprite"], .pokemonicon, .sprite').forEach((el, i) => {
  console.log(i + ':', el.tagName, el.className, 'title:', el.title, 'alt:', el.alt);
});
```

### 6. Ver estructura completa

```javascript
// Función para explorar estructura
function exploreStructure(root, depth = 0) {
  const indent = '  '.repeat(depth);
  console.log(indent + root.tagName + '.' + root.className.split(' ')[0]);
  if (depth > 5) return;
  Array.from(root.children).forEach(child => {
    exploreStructure(child, depth + 1);
  });
}

exploreStructure(document.body || document.documentElement);
```

---

## Selectores conocidos (alternativos)

### Para lado izquierdo (jugador)
- `.left`
- `.trainer-left`
- `.player-1`
- `.p1`
- `[data-side="p1"]`

### Para lado derecho (enemigo)
- `.right`
- `.trainer-right`
- `.player-2`
- `.p2`
- `[data-side="p2"]`

### Para HP
- `.statbar-lifeline` (la barra)
- `.pokename` (nombre)
- `.hpnumber` (números de HP)
- `.level` (nivel)

---

## Template para registrar resultados

```
Fecha: ___
URL: ___
Batalla activa: ___

.selectores_encontrados:
- [selector]: [count] elementos

.elementos_encontrados:
[detalle de elementos importantes]

Pokemon aliado:
- Nombre: ___
- HP: ___
- Status: ___

Pokemon enemigo:
- Nombre: ___
- HP: ___
- Status: ___
```

---

## Notas importantes

1. Pokemon Showdown usa clases cortas y genéricas (no Bootstrap)
2. Los Pokemon activos pueden estar en `<pokemonclass>` o similar
3. El HP puede estar en atributos `data-hp` o en el `title` del elemento
4. El nombre puede estar en `.nickname` o `.pokename`