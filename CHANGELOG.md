# Changelog

---

## [1.0.1] - 2024-06-03

### Fixed
- **Error de sintaxis "Identifier 'overlay' has already been declared"**: 
  - Renombrado `content.js` a `content-script.js` para forzar actualización de caché del navegador
  - Todo el código está ahora envuelto en una IIFE para evitar conflictos de variables globales
  - Eliminada variable `overlay` que causaba declaración duplicada
  - Simplificada estructura del código (de ~650 líneas a ~220 líneas)

### Refactored
- Reescritura completa del content script
- Uso de estilos inline simples en vez de CSS externo para el overlay básico
- Implementación de función `init()` más limpia y modular

### Notes
- La extensión ahora usa `all_frames: true` en el manifest para ejecutarse también en iframes de batalla
- Compatibilidad con Pokemon Showdown que usa iframes para renderizar batallas

---

## [1.0.0] - 2024-06-02

### Added
- Extensión básica de Pokemon Showdown Assistant
- Overlay visual con información de batalla
- Sistema de detección de Pokemon activo
- Integración con popup para mostrar/ocultar overlay
- Documentación técnica en `/docs`

---

## Registro Original (Archivo de Proyecto)

Formato: `- [YYYY-MM-DD HH:MM] Tarea - Descripción`

---

## 2026-06-02

### 16:00 - Completado Middleware de Manejo de Errores
- **Tarea**: Crear middleware para manejo de errores centralizado
- **Archivos**: `core/error_handler.py`, `tests/test_error_handler.py`
- **Resultado**: ErrorHandler con registro de errores, categorización, fallbacks y decoradores
- **Tests**: 11 tests agregados, 91 tests totales pasando

### 15:55 - Completado Logging Estructurado
- **Tarea**: Implementar logging estructurado con niveles configurables
- **Archivos**: `core/logging_config.py`, `tests/test_logging.py`
- **Resultado**: BattleLogger con rotación de archivos, niveles configurables, formateo consistente
- **Tests**: 9 tests agregados

### 15:45 - Completado Análisis Win Conditions
- **Tarea**: Analizar win conditions
- **Archivos**: `core/win_condition_analyzer.py`, `tests/test_win_conditions.py`
- **Resultado**: Módulo para identificar condiciones de victoria, analizar ventaja de KOs, HP, status, hazards y sweep potential
- **Tests**: 10 tests agregados

### 15:35 - Completado Aprender de Replays
- **Tarea**: Aprender de replays
- **Archivos**: `core/replay_analyzer.py`, `tests/test_replay_analyzer.py`
- **Resultado**: Sistema de análisis de replays, detección de patrones, sugerencias de mejora
- **Tests**: 7 tests agregados

### 15:25 - Completado Simulaciones de Combate
- **Tarea**: Simulaciones de combate
- **Archivos**: `core/battle_simulator.py`, `tests/test_battle_simulator.py`
- **Resultado**: Simulador de batallas para evaluar decisiones, comparar acciones, calcular win probability
- **Tests**: 8 tests agregados

### 15:15 - Completado Analizar Metagame
- **Tarea**: Analizar metagame
- **Archivos**: `core/metagame_analyzer.py`, `tests/test_metagame.py`
- **Resultado**: Analizador de tendencias, estadísticas de Pokemon, matchups, counters
- **Tests**: 8 tests agregados

### 15:00 - Completado Calculadora de Daño
- **Tarea**: Integrar calculadora de daño
- **Archivos**: `core/damage_calculator.py`, `tests/test_damage_calculator.py`
- **Resultado**: Calculadora completa con efectividad de tipos, STAB, clima, críticos
- **Tests**: 6 tests agregados

### 14:30 - Completado Historial Visual
- **Tarea**: Historial visual
- **Archivos**: `extension/ui/history.js`, `extension/ui/overlay.js`
- **Resultado**: Panel de historial en tiempo real con iconos y eventos
- **Tests**: N/A (componente UI)

### 14:15 - Completado Exportar Historial
- **Tarea**: Exportar historial
- **Archivos**: `scripts/export_history.py`, `scripts/stats.py`
- **Resultado**: Scripts para exportar CSV y ver estadísticas
- **Tests**: N/A (scripts)

### 14:00 - Completado Tests de Integración
- **Tarea**: Tests de integración
- **Archivos**: `tests/test_integration.py`
- **Resultado**: Tests de pipeline completo, integración parser->engine->storage
- **Tests**: 8 tests agregados, 30 tests totales pasando

---

## Versión 0.1.0 - MVP (2026-06-02)

### Funcionalidades Implementadas:
- Extensión de navegador (Manifest V3)
- Modelo interno (Pokemon, Team, BattleState)
- Parser para datos de batalla
- Motor de recomendación heurístico
- Sistema de almacenamiento
- Tests unitarios (22 tests)
- Documentación técnica y de instalación