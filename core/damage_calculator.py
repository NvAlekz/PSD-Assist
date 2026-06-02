"""
Pokemon Showdown Assistant - Damage Calculator
Calculadora de daño para Pokemon Showdown
"""

from typing import Optional, Dict, Tuple
from dataclasses import dataclass


@dataclass
class DamageResult:
    """Resultado de un cálculo de daño"""
    min_damage: int
    max_damage: int
    average_damage: float
    effectiveness: float
    description: str


class DamageCalculator:
    """
    Calculadora de daño para Pokemon Showdown
    
    Implementa la fórmula de daño estándar:
    Damage = ((2 * Level / 5 + 2) * Power * A / D / 50 + 2) * Modifiers
    """
    
    # Tipo de crítico (x1.5)
    CRIT_MULTIPLIER = 1.5
    
    # STAB (Same Type Attack Bonus) (x1.5 si coincide)
    STAB_MULTIPLIER = 1.5
    
    # Valores estándar de IV/EV
    DEFAULT_IV = 31
    DEFAULT_EV = 0
    
    # Modificadores de clima
    WEATHER_MODIFIERS = {
        'sun': {'fire': 1.5, 'water': 0.5},
        'rain': {'fire': 0.5, 'water': 1.5},
        'sandstorm': None,
        'hail': None
    }
    
    def __init__(self):
        self.type_chart = self.build_type_chart()
    
    def build_type_chart(self) -> Dict:
        """Construye la tabla de tipos completa"""
        return {
            'normal': {'weak': ['fighting'], 'resist': [], 'immune': ['ghost']},
            'fire': {'weak': ['water', 'rock', 'ground'], 'resist': ['fire', 'grass', 'ice', 'bug', 'steel', 'fairy'], 'immune': []},
            'water': {'weak': ['electric', 'grass'], 'resist': ['fire', 'water', 'ice', 'steel'], 'immune': []},
            'electric': {'weak': ['ground'], 'resist': ['electric', 'flying', 'steel'], 'immune': []},
            'grass': {'weak': ['fire', 'ice', 'poison', 'flying', 'bug'], 'resist': ['water', 'electric', 'grass', 'ground'], 'immune': []},
            'ice': {'weak': ['fire', 'fighting', 'rock', 'steel'], 'resist': ['ice'], 'immune': []},
            'fighting': {'weak': ['flying', 'psychic', 'fairy'], 'resist': ['bug', 'rock', 'dark'], 'immune': []},
            'poison': {'weak': ['ground', 'psychic'], 'resist': ['grass', 'fighting', 'poison', 'bug', 'fairy'], 'immune': []},
            'ground': {'weak': ['water', 'grass', 'ice'], 'resist': ['poison', 'rock'], 'immune': ['electric']},
            'flying': {'weak': ['electric', 'ice', 'rock'], 'resist': ['grass', 'fighting', 'bug'], 'immune': ['ground']},
            'psychic': {'weak': ['bug', 'ghost', 'dark'], 'resist': ['fighting', 'psychic'], 'immune': []},
            'bug': {'weak': ['fire', 'flying', 'rock'], 'resist': ['grass', 'fighting', 'ground'], 'immune': []},
            'rock': {'weak': ['water', 'grass', 'fighting', 'ground', 'steel'], 'resist': ['normal', 'fire', 'poison', 'flying'], 'immune': []},
            'ghost': {'weak': ['ghost', 'dark'], 'resist': ['poison', 'bug'], 'immune': ['normal', 'fighting']},
            'dragon': {'weak': ['ice', 'dragon', 'fairy'], 'resist': ['fire', 'water', 'electric', 'grass'], 'immune': []},
            'dark': {'weak': ['fighting', 'bug', 'fairy'], 'resist': ['ghost', 'dark'], 'immune': ['psychic']},
            'steel': {'weak': ['fire', 'fighting', 'ground'], 'resist': ['normal', 'grass', 'ice', 'flying', 'psychic', 'bug', 'rock', 'dragon', 'steel', 'fairy'], 'immune': ['poison']},
            'fairy': {'weak': ['poison', 'steel'], 'resist': ['fighting', 'bug', 'dark'], 'immune': ['dragon']},
        }
    
    def get_effectiveness(self, move_type: str, defender_types: list) -> float:
        """Calcula la efectividad de un tipo contra los tipos del defensor"""
        if move_type not in self.type_chart:
            return 1.0
        
        effectiveness = 1.0
        for dtype in defender_types:
            if dtype in self.type_chart[move_type]['immune']:
                return 0.0
            if dtype in self.type_chart[move_type]['weak']:
                effectiveness *= 2
            elif dtype in self.type_chart[move_type]['resist']:
                effectiveness *= 0.5
        
        return effectiveness
    
    def calculate_damage(
        self,
        level: int,
        power: int,
        attack: int,
        defense: int,
        move_type: str,
        defender_types: list,
        stab: bool = False,
        critical: bool = False,
        weather: Optional[str] = None,
        target_hp: int = 100
    ) -> DamageResult:
        """
        Calcula el rango de daño
        
        Args:
            level: Nivel del Pokemon atacante
            power: Poder base del movimiento
            attack: Stat de Ataque/Especial del atacante
            defense: Stat de Defensa/Especial del defensor
            move_type: Tipo del movimiento
            defender_types: Lista de tipos del defensor
            stab: Si el movimiento tiene STAB
            critical: Si es crítico
            weather: Clima actual (sun, rain, sandstorm, hail)
            target_hp: HP máximo del objetivo
            
        Returns:
            DamageResult con min, max, promedio y descripción
        """
        # Calcular efectividad
        effectiveness = self.get_effectiveness(move_type, defender_types)
        
        # Modificadores
        targets = 1  # Siempre 1 en batallas 1v1
        screens = 1  # Sin considerar screens por ahora
        
        # Modificador crítico
        crit_mod = self.CRIT_MULTIPLIER if critical else 1.0
        
        # STAB
        stab_mod = self.STAB_MULTIPLIER if stab else 1.0
        
        # Clima
        weather_mod = 1.0
        if weather and weather in self.WEATHER_MODIFIERS:
            if move_type in self.WEATHER_MODIFIERS[weather]:
                weather_mod = self.WEATHER_MODIFIERS[weather][move_type]
        
        # Otros modificadores
        other_mod = 1.0
        
        # Calcular daño base
        # Damage = (((2 * Level / 5 + 2) * Power * A / D / 50) + 2) * Modifiers
        base = ((2 * level / 5 + 2) * power * attack / defense / 50 + 2)
        
        # Aplicar modificadores
        damage = base * crit_mod * stab_mod * effectiveness * weather_mod * other_mod * targets * (1 / screens)
        
        # Rangos de daño (85% - 100%)
        min_damage = int(damage * 0.85)
        max_damage = int(damage)
        
        # Asegurar que no exceda el HP del objetivo
        max_damage = min(max_damage, target_hp)
        
        # Porcentaje de daño
        damage_percent = (damage / target_hp) * 100 if target_hp > 0 else 0
        
        # Descripción
        desc = self.build_description(move_type, effectiveness, stab, critical, weather)
        
        return DamageResult(
            min_damage=min_damage,
            max_damage=max_damage,
            average_damage=damage,
            effectiveness=effectiveness,
            description=desc
        )
    
    def build_description(
        self,
        move_type: str,
        effectiveness: float,
        stab: bool,
        critical: bool,
        weather: Optional[str]
    ) -> str:
        """Construye una descripción del daño"""
        parts = []
        
        # Efectividad
        if effectiveness == 0:
            return "No tiene efecto"
        elif effectiveness >= 4:
            parts.append("¡Superefectivo 4x!")
        elif effectiveness >= 2:
            parts.append("¡Superefectivo!")
        elif effectiveness <= 0.5:
            parts.append("No es muy efectivo")
        
        # STAB
        if stab:
            parts.append("STAB")
        
        # Crítico
        if critical:
            parts.append("¡Crítico!")
        
        # Clima
        if weather:
            weather_names = {'sun': 'sol', 'rain': 'lluvia', 'sandstorm': 'tormenta de arena', 'hail': 'granizo'}
            parts.append(f"Clima: {weather_names.get(weather, weather)}")
        
        return " ".join(parts)
    
    def calculate_ohko_chance(
        self,
        level: int,
        power: int,
        attack: int,
        defense: int,
        move_type: str,
        defender_types: list,
        stab: bool = False
    ) -> float:
        """
        Calcula la probabilidad de OHKO (One Hit KO)
        
        Solo aplica a movimientos de precisión 30 o menos
        que no son superefectivos
        """
        effectiveness = self.get_effectiveness(move_type, defender_types)
        
        # No aplica si es superefectivo
        if effectiveness > 1:
            return 0.0
        
        # Movimiento de OHKO (Fissure, Horn Drill, Guillotine)
        base = ((2 * level / 5 + 2) * power * attack / defense / 50 + 2)
        
        # Si el daño base ya supera 1.5x el HP, es siempre OHKO
        if base >= 1.5:
            return 1.0
        
        return 0.0
    
    def estimate_damage_percent(
        self,
        attacker_level: int,
        move_power: int,
        attacker_types: list,
        defender_types: list
    ) -> float:
        """
        Estima el porcentaje de daño sin stats completos
        
        Usa heurísticas para estimación rápida
        """
        # Efectividad
        effectiveness = self.get_effectiveness(
            attacker_types[0] if attacker_types else 'normal',
            defender_types
        )
        
        # Poder base promedio asumiendo nivel 50
        base_damage = (2 * attacker_level / 5 + 2) * move_power / 100 * 50 + 2
        
        # STAB
        if attacker_types and defender_types:
            if attacker_types[0] in defender_types:
                base_damage *= 1.5
        
        return min(100, base_damage * effectiveness)


class SimpleDamageCalculator:
    """
    Calculadora simplificada para uso rápido
    """
    
    def estimate(self, move_name: str, attacker_level: int = 50) -> int:
        """Estima el poder base de un movimiento"""
        high_power = {
            'hyper-beam': 150, 'overheat': 130, 'hydro-pump': 110,
            'thunder': 110, 'blizzard': 110, 'fire-blast': 110,
            'focus-blast': 120, 'earthquake': 100, 'stone-edge': 100,
            'close-combat': 120, 'flare-blitz': 120, 'bolt-strike': 120,
            'dragon-dance': 0, 'swords-dance': 0, 'calm-mind': 0,
        }
        
        medium_power = {
            'thunderbolt': 90, 'flamethrower': 90, 'ice-beam': 90,
            'surf': 90, 'psychic': 90, 'shadow-ball': 80,
            'dragon-pulse': 85, 'energy-ball': 90, 'aura-sphere': 80,
            'crunch': 80, 'x-scissor': 80, 'bug-buzz': 90,
        }
        
        low_power = {
            'quick-attack': 40, 'return': 80, 'facade': 70,
            'Body Slam': 85, 'seed-bomb': 80, 'drain-punch': 75,
        }
        
        name_lower = move_name.lower().replace('-', '').replace(' ', '')
        
        for move, power in high_power.items():
            if move in name_lower or name_lower in move:
                return power
        
        for move, power in medium_power.items():
            if move in name_lower or name_lower in move:
                return power
        
        for move, power in low_power.items():
            if move in name_lower or name_lower in move:
                return power
        
        return 40  # Poder default