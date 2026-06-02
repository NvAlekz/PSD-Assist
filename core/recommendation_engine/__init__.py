"""
Pokemon Showdown Assistant - Recommendation Engine
Motor de recomendación de jugadas
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from ..battle_state import BattleState, Pokemon


@dataclass
class Recommendation:
    """Recomendación de una jugada"""
    move: str
    target: Optional[str] = None
    score: float = 0.0
    reason: str = ""
    priority: int = 1
    
    def to_dict(self) -> Dict:
        return {
            'move': self.move,
            'target': self.target,
            'score': self.score,
            'reason': self.reason,
            'priority': self.priority
        }


class RecommendationEngine:
    """
    Motor de decisión para recomendar jugadas
    
    Usa heurísticas basadas en:
    - HP actual
    - Estados alterados
    - Efectividad de tipos
    - Peligro de movimientos enemigos
    """
    
    def __init__(self):
        self.weights = {
            'super_effective': 30,
            'not_very_effective': -20,
            'neutral': 10,
            'ohko': 50,
            'hp_damage': 15,
            'status_heal': 40,
            'switch_danger': 25,
            'setup': 20,
        }
    
    def get_recommendations(self, state: BattleState, max_results: int = 3) -> List[Recommendation]:
        """
        Obtiene las mejores recomendaciones para el estado actual
        
        Args:
            state: Estado actual de la batalla
            max_results: Número máximo de recomendaciones
            
        Returns:
            Lista ordenada de recomendaciones
        """
        if not state.my_active or not state.enemy_active:
            return []
        
        recommendations = []
        
        # Evaluar movimientos
        move_recs = self.evaluate_moves(state)
        recommendations.extend(move_recs)
        
        # Evaluar cambios
        switch_recs = self.evaluate_switches(state)
        recommendations.extend(switch_recs)
        
        # Ordenar por score y retornar top
        recommendations.sort(key=lambda x: x.score, reverse=True)
        
        # Asignar prioridad (1 = mejor)
        for i, rec in enumerate(recommendations[:max_results]):
            rec.priority = i + 1
        
        return recommendations[:max_results]
    
    def evaluate_moves(self, state: BattleState) -> List[Recommendation]:
        """Evalúa todos los movimientos disponibles"""
        recommendations = []
        my_pkm = state.my_active
        enemy_pkm = state.enemy_active
        
        if not my_pkm or not my_pkm.moves:
            return recommendations
        
        for move in my_pkm.moves:
            score, reason = self.evaluate_single_move(move, state)
            recommendations.append(Recommendation(
                move=move,
                score=score,
                reason=reason
            ))
        
        return recommendations
    
    def evaluate_single_move(self, move: str, state: BattleState) -> Tuple[float, str]:
        """
        Evalúa un movimiento individual
        
        Returns:
            Tuple de (score, reason)
        """
        score = self.weights['neutral']
        reasons = []
        
        my_pkm = state.my_active
        enemy_pkm = state.enemy_active
        
        # Calcular efectividad base
        effectiveness = enemy_pkm.get_type_effectiveness(self.get_move_type(move))
        
        if effectiveness >= 2:
            score += self.weights['super_effective']
            reasons.append('Superefectivo')
        elif effectiveness <= 0.5:
            score += self.weights['not_very_effective']
            reasons.append('Poco efectivo')
        
        # Bonus por OHKO potential
        if 'fissure' in move.lower() or 'horn-drill' in move.lower() or 'guillotine' in move.lower():
            if effectiveness >= 2:
                score += self.weights['ohko']
                reasons.append('Potencial OHKO')
        
        # Daño estimado basado en HP
        damage_percent = self.estimate_damage(move, my_pkm, enemy_pkm)
        score += damage_percent * self.weights['hp_damage'] / 10
        
        if damage_percent >= 50:
            reasons.append(f'~{int(damage_percent)}% daño')
        
        reason = ', '.join(reasons) if reasons else 'Movimiento neutro'
        
        return score, reason
    
    def evaluate_switches(self, state: BattleState) -> List[Recommendation]:
        """Evalúa opciones de cambio"""
        recommendations = []
        my_pkm = state.my_active
        enemy_pkm = state.enemy_active
        
        if not state.my_can_switch:
            return recommendations
        
        for switch_pkm in state.my_team.get_available_switches():
            if switch_pkm.name == my_pkm.name:
                continue
            
            score, reason = self.evaluate_switch(switch_pkm, state)
            recommendations.append(Recommendation(
                move=f'Cambiar a {switch_pkm.name}',
                target=switch_pkm.name,
                score=score,
                reason=reason
            ))
        
        return recommendations
    
    def evaluate_switch(self, new_pkm: Pokemon, state: BattleState) -> Tuple[float, str]:
        """Evalúa un cambio específico"""
        score = 0
        reasons = []
        
        # Peligro del Pokemon actual
        danger = self.calculate_danger(state.my_active, state.enemy_active)
        if danger > 50:
            score += self.weights['switch_danger'] * (danger / 100)
            reasons.append('Peligro alto')
        
        # HP bajo del Pokemon actual
        if state.my_active.hp_percent <= 25:
            score += 20
            reasons.append('HP bajo, necesita cambio')
        
        # Estados alterados que impiden atacar
        if state.my_active.status.value in ['sleep', 'freeze', 'confusion']:
            score += 30
            reasons.append(f'Estado: {state.my_active.status.value}')
        
        # Ventaja de tipo del nuevo Pokemon
        enemy_type = state.enemy_active.types[0] if state.enemy_active.types else 'normal'
        for ptype in new_pkm.types:
            if ptype == 'ground' and enemy_type == 'electric':
                score += 15
                reasons.append('Inmune a eléctrico')
            elif ptype == 'water' and enemy_type == 'fire':
                score += 10
                reasons.append('Ventaja de tipo')
        
        reason = ', '.join(reasons) if reasons else 'Cambio seguro'
        
        return score, reason
    
    def calculate_danger(self, my_pkm: Pokemon, enemy_pkm: Pokemon) -> float:
        """Calcula el nivel de peligro (0-100)"""
        if not my_pkm or not enemy_pkm:
            return 0
        
        danger = 0
        
        # HP bajo = más peligro
        danger += (100 - my_pkm.hp_percent) * 0.3
        
        # Estados que impiden atacar
        if my_pkm.status.value in ['sleep', 'freeze']:
            danger += 30
        
        # Peligro del enemigo basado en efectividad
        for ptype in enemy_pkm.types:
            effectiveness = my_pkm.get_type_effectiveness(ptype)
            if effectiveness >= 2:
                danger += 20
        
        return min(100, danger)
    
    def get_move_type(self, move: str) -> str:
        """Determina el tipo de un movimiento"""
        type_moves = {
            'electric': ['thunderbolt', 'thunder', 'volt-tackle', 'thunder-shock', 'charge-beam'],
            'fire': ['flamethrower', 'fire-blast', 'fire-punch', 'ember', 'fire-fang'],
            'water': ['surf', 'hydropump', 'water-gun', 'aqua-jet', 'scald'],
            'grass': ['solar-beam', 'energy-ball', 'grass-knot', 'leech-seed', 'grass-pledge'],
            'ice': ['ice-beam', 'ice-punch', 'blizzard', 'ice-fang', 'frost-breath'],
            'fighting': ['close-combat', 'focus-blast', 'low-sweep', 'aura-sphere', 'dynamic-punch'],
            'psychic': ['psychic', 'psyshock', 'shadow-ball', 'futuresight', 'psybeam'],
            'ghost': ['shadow-ball', 'shadow-claw', 'phantom-force', 'hex', 'night-shade'],
            'dragon': ['dragon-pulse', 'draco-meteor', 'outrage', 'dragon-claw', 'dragon-tail'],
            'dark': ['dark-pulse', 'crunch', 'sucker-punch', 'knock-off', 'thief'],
            'normal': ['hyper-beam', 'body-slam', 'quick-attack', 'return', 'facade'],
        }
        
        move_lower = move.lower().replace('-', '').replace(' ', '')
        
        for mtype, moves in type_moves.items():
            for m in moves:
                if m in move_lower or move_lower in m:
                    return mtype
        
        return 'normal'
    
    def estimate_damage(self, move: str, attacker: Pokemon, defender: Pokemon) -> float:
        """
        Estima el porcentaje de daño de un movimiento
        (Heurística simplificada sin calculadora completa)
        """
        base_power = self.get_base_power(move)
        effectiveness = defender.get_type_effectiveness(self.get_move_type(move))
        
        # Estimación muy simplificada
        avg_multiplier = sum(effectiveness for t in defender.types) / max(len(defender.types), 1)
        
        # Daño base aproximado (asumiendo IVs 31, EVs 0, nivel 100)
        estimated_damage = (base_power * 0.4 + 2) / defender.max_hp * 50 * avg_multiplier
        
        return min(100, estimated_damage * effectiveness)
    
    def get_base_power(self, move: str) -> int:
        """Obtiene poder base estimado de un movimiento"""
        high_power = ['hyper-beam', 'overheat', 'blast-burn', 'hydro-cannon', 'frenzy-plant',
                      'giga-impact', 'dragon-dance', 'earthquake', 'stone-edge', 'close-combat',
                      'superpower', 'flare-blitz', 'bolt-strike', 'v-create', 'fissure', 'horn-drill', 'guillotine']
        
        medium_power = ['flamethrower', 'thunderbolt', 'ice-beam', 'surf', 'psychic', 'shadow-ball',
                        'dragon-pulse', 'focus-blast', 'fire-blast', 'thunder', 'blizzard', 'solar-beam']
        
        move_lower = move.lower()
        
        for m in high_power:
            if m in move_lower:
                return 150
        
        for m in medium_power:
            if m in move_lower:
                return 90
        
        return 40  # Poder base default