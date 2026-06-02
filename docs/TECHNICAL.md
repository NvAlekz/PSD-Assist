# Documentación Técnica - Pokemon Showdown Assistant

## Visión General

El asistente analiza el estado de la batalla en Pokemon Showdown y recomienda jugadas basadas en heurísticas.

## Arquitectura

### Módulos Principales

#### 1. Extension (Navegador)

**Content Script** (`extension/content/content.js`)
- Lee el DOM directamente de Pokemon Showdown
- Detecta: Pokemon activos, HP, estados, movimientos
- Envía datos al background service worker

**Background Service** (`extension/background/background.js`)
- Recibe actualizaciones de estado
- Almacena estado de batallas por tab
- Comunica con popup

**Popup** (`extension/popup/`)
- Interface de control del asistente
- Muestra estado de batalla activa
- Permite togglear el overlay

#### 2. Core (Lógica de Negocio)

**BattleState** (`core/battle_state/battle_state.py`)
- Estado completo de una batalla
- Equipos aliados y enemigos
- Hazards del campo
- Historial de turnos

**Pokemon** (`core/battle_state/pokemon.py`)
- Modelo de Pokemon individual
- HP, estado, tipos, movimientos
- Cálculo de efectividad de tipos

**Team** (`core/battle_state/team.py`)
- Colección de Pokemon
- Tracking de Pokemon disponibles

**Parser** (`core/parser/__init__.py`)
- Parsea datos crudos del DOM
- Convierte a modelos internos

**RecommendationEngine** (`core/recommendation_engine/__init__.py`)
- Evalúa movimientos y cambios
- Ranking de opciones
- Score basado en efectividad

**Storage** (`core/storage/__init__.py`)
- Persistencia de batallas
- Exportación a CSV
- Estadísticas

## Flujo de Datos

```
[DOM Pokemon Showdown]
        ↓
[Content Script] → Extrae datos del DOM
        ↓
[Background Service] → Almacena estado
        ↓
[Core Python] → Procesa y analiza
        ↓
[Overlay] → Muestra recomendaciones
```

## Sistema de Recomendación

### Algoritmo de Evaluación

1. **Evaluación de Movimientos**
   - Calcula efectividad de tipos
   - Estima daño basado en poder base
   - Bonus por superefectividad

2. **Evaluación de Cambios**
   - Evalúa peligro actual (HP bajo, estados)
   - Calcula ventaja de tipo del nuevo Pokemon
   - Considera immunity (Ground vs Electric)

3. **Ranking Final**
   - Combina scores de movimientos y cambios
   - Ordena por score descendente
   - Retorna top 3 recomendaciones

### Pesos Configurables

```python
weights = {
    'super_effective': 30,    # +30 por superefectividad
    'not_very_effective': -20,  # -20 por no muy efectivo
    'neutral': 10,           # +10 movimiento neutro
    'ohko': 50,              # +50 potencial OHKO
    'hp_damage': 15,         # +15 por % de daño
    'status_heal': 40,       # +40 por curar estado
    'switch_danger': 25,    # +25 por cambio urgente
    'setup': 20,             # +20 por setup
}
```

## API Pública

### RecomendationEngine

```python
engine = RecommendationEngine()

# Obtener recomendaciones
recommendations = engine.get_recommendations(state, max_results=3)

# Cada recomendación tiene:
# - move: nombre del movimiento o acción
# - score: puntuación (mayor es mejor)
# - reason: explicación breve
# - priority: ranking (1 = mejor)
```

### BattleState

```python
state = BattleState()

# Estado actual
state.my_active       # Pokemon aliado activo
state.enemy_active    # Pokemon enemigo activo
state.turn            # Turno actual

# Equipos
state.my_team.pokemons       # Lista de Pokemon aliados
state.enemy_team.pokemons    # Lista de Pokemon enemigos
state.my_team.remaining_count  # Pokemon restantes

# Hazards
state.my_hazards.spikes      # 0-3 capas de spikes
state.my_hazards.stealth_rock  # True/False
```

## Tests

Ejecutar tests:
```bash
python -m unittest tests.test_core -v
```

Verificar cobertura:
```bash
python -m unittest discover -v
```