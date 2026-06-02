"""
Pokemon Showdown Assistant - Win Condition Analyzer
Analiza las condiciones de victoria en una batalla
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class WinCondition:
    """Representa una condición de victoria"""
    type: str  # 'ko', 'status', 'hazard', 'weather', 'sweep', 'stall'
    description: str
    priority: float
    probability: float
    remaining_turns: Optional[int] = None


class WinConditionAnalyzer:
    """
    Analizador de condiciones de victoria
    
    Identifica y evalúa diferentes paths hacia la victoria
    """
    
    # Pesos para calcular probabilidad de victoria
    WEIGHTS = {
        'ko_advantage': 30,
        'status_advantage': 15,
        'hazard_damage': 10,
        'weather_turns': 5,
        'team_advantage': 25,
        'hp_advantage': 20,
    }
    
    def __init__(self):
        self.conditions = []
    
    def analyze(self, battle_state) -> List[WinCondition]:
        """
        Analiza el estado de la batalla y genera condiciones de victoria
        
        Args:
            battle_state: Estado actual de la batalla
            
        Returns:
            Lista de condiciones de victoria ordenadas por prioridad
        """
        conditions = []
        
        # 1. Analizar ventaja de KOs
        ko_condition = self.analyze_ko_advantage(battle_state)
        if ko_condition:
            conditions.append(ko_condition)
        
        # 2. Analizar ventaja de HP
        hp_condition = self.analyze_hp_advantage(battle_state)
        if hp_condition:
            conditions.append(hp_condition)
        
        # 3. Analizar status como win condition
        status_condition = self.analyze_status_conditions(battle_state)
        if status_condition:
            conditions.append(status_condition)
        
        # 4. Analizar hazards
        hazard_condition = self.analyze_hazards(battle_state)
        if hazard_condition:
            conditions.append(hazard_condition)
        
        # 5. Analizar sweep potential
        sweep_condition = self.analyze_sweep_potential(battle_state)
        if sweep_condition:
            conditions.append(sweep_condition)
        
        # Ordenar por probabilidad * prioridad
        conditions.sort(key=lambda x: x.probability * x.priority, reverse=True)
        
        return conditions[:5]  # Top 5 condiciones
    
    def analyze_ko_advantage(self, state) -> Optional[WinCondition]:
        """Analiza ventaja de KOs entre equipos"""
        my_alive = state.my_team.remaining_count
        enemy_alive = state.enemy_team.remaining_count
        
        ko_diff = my_alive - enemy_alive
        
        if ko_diff > 0:
            return WinCondition(
                type='ko',
                description=f"Ventaja de {ko_diff} Pokemon(s) vivo(s)",
                priority=1.0,
                probability=min(1.0, 0.5 + (ko_diff * 0.15))
            )
        elif ko_diff < 0:
            return WinCondition(
                type='ko',
                description=f"Enemigo tiene {abs(ko_diff)} Pokemon(s) más vivo(s)",
                priority=0.3,
                probability=max(0.0, 0.5 + (ko_diff * 0.15))
            )
        
        return None
    
    def analyze_hp_advantage(self, state) -> Optional[WinCondition]:
        """Analiza ventaja de HP total"""
        my_total_hp = sum(p.hp for p in state.my_team.pokemons if not p.fainted)
        enemy_total_hp = sum(p.hp for p in state.enemy_team.pokemons if not p.fainted)
        
        total_hp_diff = my_total_hp - enemy_total_hp
        max_hp = max(my_total_hp + enemy_total_hp, 1)
        
        if abs(total_hp_diff) < max_hp * 0.1:
            return None  # No hay ventaja significativa
        
        if total_hp_diff > 0:
            return WinCondition(
                type='hp',
                description=f"Ventaja de {total_hp_diff} HP total",
                priority=0.7,
                probability=0.5 + (total_hp_diff / max_hp) * 0.5
            )
        
        return None
    
    def analyze_status_conditions(self, state) -> Optional[WinCondition]:
        """Analiza condiciones de victoria por estados"""
        my_statused = sum(1 for p in state.enemy_team.pokemons if p.status.value != 'none')
        enemy_statused = sum(1 for p in state.my_team.pokemons if p.status.value != 'none')
        
        status_adv = my_statused - enemy_statused
        
        if status_adv > 0:
            # Verificar si el status es fatal (toxic + low hp)
            toxic_threat = any(
                p.status.value == 'toxic' and p.hp_percent < 50
                for p in state.enemy_team.pokemons
            )
            
            prob = 0.5 + (status_adv * 0.1)
            if toxic_threat:
                prob += 0.2
            
            return WinCondition(
                type='status',
                description=f"{status_adv} Pokemon(s) enemigo(s) con estado alterado",
                priority=0.8,
                probability=min(0.95, prob)
            )
        
        return None
    
    def analyze_hazards(self, state) -> Optional[WinCondition]:
        """Analiza condiciones de victoria por hazards"""
        my_hazard_count = (
            state.enemy_hazards.spikes +
            state.enemy_hazards.toxic_spikes +
            (1 if state.enemy_hazards.stealth_rock else 0) +
            (1 if state.enemy_hazards.sticky_web else 0)
        )
        
        enemy_hazard_count = (
            state.my_hazards.spikes +
            state.my_hazards.toxic_spikes +
            (1 if state.my_hazards.stealth_rock else 0) +
            (1 if state.my_hazards.sticky_web else 0)
        )
        
        hazard_adv = my_hazard_count - enemy_hazard_count
        
        if hazard_adv > 0:
            damage = self.estimate_hazard_damage(hazard_adv)
            return WinCondition(
                type='hazard',
                description=f"{my_hazard_count} capas de hazards en campo enemigo ({damage}% daño por entrada)",
                priority=0.5,
                probability=0.5 + (hazard_adv * 0.1)
            )
        
        return None
    
    def analyze_sweep_potential(self, state) -> Optional[WinCondition]:
        """Analiza potencial de sweep"""
        # Buscar Pokemon con HP alto y buena posición
        my_sweepers = [
            p for p in state.my_team.pokemons
            if not p.fainted and p.hp_percent >= 75
        ]
        enemy_sweepers = [
            p for p in state.enemy_team.pokemons
            if not p.fainted and p.hp_percent >= 75
        ]
        
        if len(my_sweepers) > len(enemy_sweepers):
            sweeper = my_sweepers[0]
            return WinCondition(
                type='sweep',
                description=f"{sweeper.name} tiene potencial de sweep ({sweeper.hp_percent}% HP)",
                priority=0.9,
                probability=0.6 + (len(my_sweepers) * 0.05)
            )
        
        return None
    
    def estimate_hazard_damage(self, layer_count: int) -> int:
        """Estima daño por layer de hazard"""
        damage_map = {
            1: 12,   # 1 layer Spikes
            2: 18,   # 2 layers Spikes
            3: 25,   # 3 layers Spikes
            4: 25,   # Stealth Rock
            5: 25,   # Sticky Web
        }
        
        return damage_map.get(layer_count, layer_count * 8)
    
    def get_win_probability(self, battle_state) -> float:
        """
        Calcula probabilidad general de victoria
        
        Returns:
            Probabilidad entre 0.0 y 1.0
        """
        conditions = self.analyze(battle_state)
        
        if not conditions:
            return 0.5  # 50% si no hay condiciones claras
        
        # Ponderar por probabilidad y prioridad
        total_weight = 0
        weighted_sum = 0
        
        for cond in conditions:
            weight = cond.priority * cond.probability
            weighted_sum += weight
            total_weight += cond.priority
        
        if total_weight == 0:
            return 0.5
        
        return max(0.1, min(0.9, weighted_sum / total_weight))
    
    def suggest_next_action(self, battle_state) -> Dict:
        """
        Sugiere la siguiente acción basada en win conditions
        
        Returns:
            Diccionario con sugerencia
        """
        conditions = self.analyze(battle_state)
        
        if not conditions:
            return {
                'action': 'attack',
                'target': 'any',
                'reason': 'Sin condiciones claras'
            }
        
        top_condition = conditions[0]
        
        if top_condition.type == 'sweep':
            return {
                'action': 'attack',
                'target': 'enemy_active',
                'reason': f"Potencial de sweep: {top_condition.description}"
            }
        
        if top_condition.type == 'ko':
            return {
                'action': 'attack',
                'target': 'lowest_hp',
                'reason': f"Ventaja de KOs: {top_condition.description}"
            }
        
        if top_condition.type == 'status':
            return {
                'action': 'status',
                'target': 'enemy_active',
                'reason': f"Condición de estado: {top_condition.description}"
            }
        
        if top_condition.type == 'hazard':
            return {
                'action': 'hazard',
                'target': 'enemy_field',
                'reason': f"Condición de hazards: {top_condition.description}"
            }
        
        return {
            'action': 'attack',
            'target': 'any',
            'reason': 'Acción predeterminada'
        }