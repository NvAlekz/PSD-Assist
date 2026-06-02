# Guía de Instalación - Pokemon Showdown Assistant

## Requisitos

- Navegador compatible con extensiones Manifest V3 (Chrome 88+, Edge 88+, Firefox 78+)
- Python 3.8+ (para ejecutar el core si se usa standalone)
- Node.js (opcional, para desarrollo de la extensión)

## Instalación de la Extensión

### Chrome / Edge

1. Descarga o clona el repositorio
2. Abre `chrome://extensions/`
3. Activa el "Modo de desarrollador"
4. Click en "Cargar descomprimida"
5. Selecciona la carpeta `extension/`

### Firefox

1. Abre `about:debugging`
2. Click en "Este Firefox"
3. Click en "Cargar временную надстройку"
4. Selecciona cualquier archivo en `extension/`

## Estructura del Proyecto

```
PSD-Assist/
├── extension/           # Extensión de navegador
│   ├── manifest.json    # Configuración de la extensión
│   ├── background/      # Service worker
│   ├── content/         # Content script (DOM parsing)
│   └── popup/           # UI del popup
├── core/                # Núcleo Python
│   ├── battle_state/    # Modelos de datos
│   ├── parser/          # Parser de datos
│   ├── recommendation_engine/  # Motor de decisión
│   └── storage/         # Persistencia
├── ui/                  # Interfaces adicionales
├── tests/               # Tests unitarios
└── docs/                # Documentación
```

## Uso

1. Instala la extensión en tu navegador
2. Abre Pokemon Showdown (https://play.pokemonshowdown.com/)
3. Comienza una batalla
4. El overlay aparecerá mostrando recomendaciones

## Configuración

### Habilitar/Deshabilitar

Usa el popup de la extensión para activar/desactivar el asistente.

### Personalizar

Edita `extension/content/styles.css` para cambiar la apariencia del overlay.

## Solución de Problemas

### La extensión no aparece
- Verifica que la extensión esté habilitada en `chrome://extensions/`
- Revisa la consola del navegador (`F12`) para errores

### El overlay no se muestra
- Asegúrate de estar en una batalla activa
- Verifica que los selectores CSS del DOM coincidan con la versión actual de PS

### Las recomendaciones no son precisas
- El sistema usa heurísticas básicas
- Para mejor precisión, se requiere la calculadora de daño completa (FASE 8)