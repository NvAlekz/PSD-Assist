"""
Pokemon Showdown Assistant - Battle Simulator
Simulador de combate para evaluar decisiones
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import random


@dataclass
class SimulationResult:
    """Resultado de una simulación"""
    action: str
    win_probability: float
    expected_damage: float
    risk_level: float  # 0-1, mayor = más riesgoso
    turns_to_ko: Optional[int] = None
    alternative: Optional[str] = None


class BattleSimulator:
    """
    Simulador de batallas Pokemon
    
    Permite simular diferentes acciones y evaluar
    sus consecuencias antes de tomar una decisión
    """
    
    def __init__(self):
        self.current_simulations = []
    
    def simulate_move(
        self,
        attacker: Dict,
        defender: Dict,
        move: str,
        iterations: int = 100
    ) -> SimulationResult:
        """
        Simula un movimiento múltiples veces
        
        Args:
            attacker: Datos del Pokemon atacante
            defender: Datos del Pokemon defensor
            move: Nombre del movimiento
            iterations: Número de simulaciones
            
        Returns:
            SimulationResult con estadísticas
        """
        wins = 0
        total_damage = 0
        ko_turns = []
        
        for _ in range(iterations):
            damage = self._calculate_damage(attacker, defender, move)
            total_damage += damage
            
            # Estimar si causa KO
            defender_hp = defender.get('hp', 100)
            if damage >= defender_hp:
                wins += 1
                ko_turns.append(random.randint(1, 3))
        
        avg_damage = total_damage / iterations
        win_prob = wins / iterations
        avg_ko_turn = sum(ko_turns) / len(ko_turns) if ko_turns else None
        
        # Calcular riesgo (basado en varianza)
        damages = [self._calculate_damage(attacker, defender, move) for _ in range(20)]
        variance = sum((d - avg_damage) ** 2 for d in damages) / len(damages)
        risk = min(1.0, variance / (avg_damage ** 2 + 1))
        
        return SimulationResult(
            action=move,
            win_probability=win_prob,
            expected_damage=avg_damage,
            risk_level=risk,
            turns_to_ko=avg_ko_turn
        )
    
    def _calculate_damage(
        self,
        attacker: Dict,
        defender: Dict,
        move: str
    ) -> float:
        """Calcula daño pseudo-aleatorio"""
        base_damage = random.randint(30, 100)
        attack = attacker.get('attack', 80)
        defense = defender.get('defense', 80)
        
        damage = (base_damage * attack / defense) * random.uniform(0.85, 1.0)
        return damage
    
    def simulate_switch(
        self,
        new_pokemon: Dict,
        enemy_pokemon: Dict,
        iterations: int = 100
    ) -> SimulationResult:
        """
        Simula un cambio de Pokemon
        
        Returns:
            SimulationResult con análisis del switch
        """
        safe_switches = 0
        expected_survival = 0
        
        for _ in range(iterations):
            # Simular si el switch sobrevive
            enemy_damage = random.randint(20, 80)
            new_hp = new_pokemon.get('hp', 100)
            
            if new_hp > enemy_damage:
                safe_switches += 1
                expected_survival += new_hp - enemy_damage
        
        win_prob = safe_switches / iterations
        avg_survival = expected_survival / iterations
        
        return SimulationResult(
            action=f"Switch to {new_pokemon.get('name', 'Unknown')}",
            win_probability=win_prob,
            expected_damage=avg_survival,
            risk_level=1 - win_prob
        )
    
    def compare_actions(
        self,
        state: Dict,
        actions: List[str]
    ) -> List[SimulationResult]:
        """
        Compara múltiples acciones y retorna ranking
        
        Args:
            state: Estado actual de la batalla
            actions: Lista de acciones a comparar
            
        Returns:
            Lista ordenada de SimulationResult por win_probability
        """
        results = []
        
        for action in actions:
            if 'switch' in action.lower():
                # Extraer nombre del Pokemon
                pkm_name = action.replace('switch', '').replace('to', '').strip()
                result = self.simulate_switch(
                    {'name': pkm_name, 'hp': 100},
                    state.get('enemy', {}),
                    iterations=50
                )
            else:
                result = self.simulate_move(
                    state.get('attacker', {}),
                    state.get('defender', {}),
                    action,
                    iterations=50
                )
            
            results.append(result)
        
        # Ordenar por win_probability descendente
        results.sort(key=lambda x: x.win_probability, reverse=True)
        
        # Agregar alternativas a las no-óptimas
        for i, result in enumerate(results):
            if i > 0 and result.win_probability < results[0].win_probability * 0.8:
                result.alternative = f"Consider {results[0].action} instead ({(results[0].win_probability - result.win_probability) * 100:.1f}% better)"
        
        return results
    
    def simulate_full_battle(
        self,
        player_team: List[Dict],
        enemy_team: List[Dict],
        max_turns: int = 50
    ) -> Dict:
        """
        Simula una batalla completa
        
        Returns:
            Diccionario con resultado de la simulación
        """
        player_hp = [pkm.get('hp', 100) for pkm in player_team]
        enemy_hp = [pkm.get('hp', 100) for pkm in enemy_team]
        
        player_active = 0
        enemy_active = 0
        
        for turn in range(max_turns):
            # Turno del jugador
            if player_hp[player_active] <= 0:
                player_active = self._next_alive(player_hp, player_active)
                if player_active is None:
                    return {'winner': 'enemy', 'turns': turn, 'reason': 'No Pokemon remaining'}
            
            # Turno del enemigo
            if enemy_hp[enemy_active] <= 0:
                enemy_active = self._next_alive(enemy_hp, enemy_active)
                if enemy_active is None:
                    return {'winner': 'player', 'turns': turn, 'reason': 'All enemy KO'}
            
            # Simular daño mutuo
            player_damage = random.randint(15, 45)
            enemy_damage = random.randint(15, 45)
            
            enemy_hp[enemy_active] -= player_damage
            player_hp[player_active] -= enemy_damage
        
        # Máximo de turnos alcanzado
        player_remaining = sum(1 for hp in player_hp if hp > 0)
        enemy_remaining = sum(1 for hp in enemy_hp if hp > 0)
        
        return {
            'winner': 'player' if player_remaining > enemy_remaining else 'enemy',
            'turns': max_turns,
            'player_remaining': player_remaining,
            'enemy_remaining': enemy_remaining,
            'reason': 'Time limit'
        }
    
    def _next_alive(self, hp_list: List[int], current: int) -> Optional[int]:
        """Encuentra el siguiente Pokemon vivo"""
        n = len(hp_list)
        for i in range(n):
            idx = (current + 1 + i) % n
            if hp_list[idx] > 0:
                return idx
        return None
    
    def get_recommendation(self, state: Dict, available_actions: List[str]) -> Dict:
        """
        Obtiene recomendación basada en simulación
        
        Returns:
            Diccionario con mejor acción y explicación
        """
        if not available_actions:
            return {'action': 'pass', 'reason': 'No actions available'}
        
        comparisons = self.compare_actions(state, available_actions)
        best = comparisons[0]
        
        # Construir recomendación
        recommendation = {
            'action': best.action,
            'win_probability': f"{best.win_probability * 100:.1f}%",
            'expected_damage': f"{best.expected_damage:.1f}",
            'risk': 'Low' if best.risk_level < 0.3 else 'Medium' if best.risk_level < 0.6 else 'High'
        }
        
        if best.alternative:
            recommendation['alternative'] = best.alternative
        
        return recommendation