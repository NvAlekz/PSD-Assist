"""
Pokemon Showdown Assistant - Battle State
Estado completo de una batalla
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from .pokemon import Pokemon
from .team import Team


@dataclass
class Hazards:
    """Hazard tracking para el campo"""
    spikes: int = 0
    toxic_spikes: int = 0
    stealth_rock: bool = False
    sticky_web: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'spikes': self.spikes,
            'toxicSpikes': self.toxic_spikes,
            'stealthRock': self.stealth_rock,
            'stickyWeb': self.sticky_web
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Hazards':
        return cls(
            spikes=data.get('spikes', 0),
            toxic_spikes=data.get('toxicSpikes', 0),
            stealth_rock=data.get('stealthRock', False),
            sticky_web=data.get('stickyWeb', False)
        )


@dataclass
class BattleState:
    """
    Estado completo de una batalla de Pokemon Showdown
    
    Attributes:
        turn: Número de turno actual
        my_team: Equipo del jugador
        enemy_team: Equipo enemigo
        my_hazards: Hazards en campo aliado
        enemy_hazards: Hazards en campo enemigo
        timestamp: Timestamp de última actualización
        battle_id: Identificador único de la batalla
    """
    turn: int = 0
    my_team: Team = field(default_factory=Team)
    enemy_team: Team = field(default_factory=Team)
    my_hazards: Hazards = field(default_factory=Hazards)
    enemy_hazards: Hazards = field(default_factory=Hazards)
    timestamp: int = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    battle_id: str = ""
    weather: Optional[str] = None
    terrain: Optional[str] = None
    
    # Historial de turnos
    turn_history: List[Dict] = field(default_factory=list)
    
    @property
    def my_active(self) -> Optional[Pokemon]:
        """Pokemon activo aliado"""
        return self.my_team.get_active()
    
    @property
    def enemy_active(self) -> Optional[Pokemon]:
        """Pokemon activo enemigo"""
        return self.enemy_team.get_active()
    
    @property
    def is_battle_over(self) -> bool:
        """Verifica si la batalla terminó"""
        return not self.my_team.is_alive or not self.enemy_team.is_alive
    
    @property
    def my_can_switch(self) -> bool:
        """Verifica si el jugador puede cambiar"""
        return len(self.my_team.get_available_switches()) > 0 and self.my_active is not None
    
    def advance_turn(self) -> None:
        """Avanza un turno"""
        self.turn += 1
        self.timestamp = int(datetime.now().timestamp() * 1000)
    
    def record_action(self, action: Dict) -> None:
        """Registra una acción en el historial"""
        self.turn_history.append({
            'turn': self.turn,
            'action': action,
            'timestamp': int(datetime.now().timestamp() * 1000)
        })
    
    def get_state_summary(self) -> Dict:
        """Resumen del estado actual"""
        return {
            'turn': self.turn,
            'myPokemon': self.my_active.name if self.my_active else None,
            'myHp': self.my_active.hp_percent if self.my_active else 0,
            'enemyPokemon': self.enemy_active.name if self.enemy_active else None,
            'enemyHp': self.enemy_active.hp_percent if self.enemy_active else 0,
            'myRemaining': self.my_team.remaining_count,
            'enemyRemaining': self.enemy_team.remaining_count
        }
    
    def to_dict(self) -> Dict:
        """Convierte el estado a diccionario"""
        return {
            'turn': self.turn,
            'myTeam': self.my_team.to_dict(),
            'enemyTeam': self.enemy_team.to_dict(),
            'myHazards': self.my_hazards.to_dict(),
            'enemyHazards': self.enemy_hazards.to_dict(),
            'timestamp': self.timestamp,
            'battleId': self.battle_id,
            'weather': self.weather,
            'terrain': self.terrain,
            'turnHistory': self.turn_history
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BattleState':
        """Crea un BattleState desde un diccionario"""
        state = cls(
            turn=data.get('turn', 0),
            timestamp=data.get('timestamp', 0),
            battle_id=data.get('battleId', ''),
            weather=data.get('weather'),
            terrain=data.get('terrain'),
            turn_history=data.get('turnHistory', [])
        )
        
        if 'myTeam' in data:
            state.my_team = Team.from_dict(data['myTeam'])
        if 'enemyTeam' in data:
            state.enemy_team = Team.from_dict(data['enemyTeam'])
        if 'myHazards' in data:
            state.my_hazards = Hazards.from_dict(data['myHazards'])
        if 'enemyHazards' in data:
            state.enemy_hazards = Hazards.from_dict(data['enemyHazards'])
        
        return state
    
    def copy(self) -> 'BattleState':
        """Crea una copia del estado"""
        return BattleState.from_dict(self.to_dict())