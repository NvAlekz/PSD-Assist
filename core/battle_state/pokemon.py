"""
Pokemon Showdown Assistant - Pokemon Model
Representa un Pokemon con todos sus atributos relevantes
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum


class Status(Enum):
    """Estados alterados posibles"""
    NONE = "none"
    BURNED = "burned"
    POISONED = "poisoned"
    TOXIC = "toxic"
    SLEEP = "sleep"
    FROZEN = "frozen"
    PARALYZED = "paralyzed"
    CONFUSED = "confused"


@dataclass
class Pokemon:
    """
    Modelo de un Pokemon en batalla
    
    Attributes:
        name: Nombre del Pokemon
        species: Especie (nombre interno)
        hp: HP actual
        max_hp: HP máximo
        level: Nivel (default 100)
        status: Estado alterado actual
        moves: Lista de movimientos disponibles
        abilities: Habilidades conocidas
        types: Tipos del Pokemon
        fainted: Si el Pokemon está debilitado
    """
    name: str
    species: str = ""
    hp: int = 100
    max_hp: int = 100
    level: int = 100
    status: Status = Status.NONE
    moves: List[str] = field(default_factory=list)
    abilities: List[str] = field(default_factory=list)
    types: List[str] = field(default_factory=list)
    fainted: bool = False
    
    def __post_init__(self):
        if not self.species:
            self.species = self.name.split(' ')[0]
        if self.hp == 0:
            self.fainted = True
    
    @property
    def hp_percent(self) -> int:
        """Calcula el porcentaje de HP"""
        if self.max_hp == 0:
            return 0
        return int((self.hp / self.max_hp) * 100)
    
    @property
    def hp_category(self) -> str:
        """Categoría de HP: high, medium, low"""
        pct = self.hp_percent
        if pct >= 50:
            return "high"
        elif pct >= 25:
            return "medium"
        return "low"
    
    def can_switch(self) -> bool:
        """Determina si el Pokemon puede ser cambiado"""
        return not self.fainted
    
    def get_type_effectiveness(self, move_type: str) -> float:
        """
        Calcula la efectividad de un tipo de movimiento
        contra este Pokemon
        """
        type_chart = {
            'fire': {'weak': ['grass'], 'resist': ['fire', 'ice', 'bug', 'steel'], 'immune': []},
            'water': {'weak': ['electric', 'grass'], 'resist': ['fire', 'water', 'steel'], 'immune': []},
            'electric': {'weak': ['ground'], 'resist': ['electric', 'flying', 'steel'], 'immune': []},
            'grass': {'weak': ['fire', 'ice', 'poison', 'flying', 'bug'], 'resist': ['water', 'electric', 'grass', 'ground'], 'immune': []},
            'ice': {'weak': ['fire', 'fighting', 'rock', 'steel'], 'resist': ['ice'], 'immune': []},
            'fighting': {'weak': ['flying', 'psychic', 'fairy'], 'resist': ['bug', 'rock', 'dark'], 'immune': []},
            'poison': {'weak': ['ground', 'psychic'], 'resist': ['grass', 'fighting', 'poison', 'bug'], 'immune': []},
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
        
        if move_type not in type_chart:
            return 1.0
        
        effectiveness = 1.0
        for ptype in self.types:
            if ptype in type_chart[move_type]['immune']:
                effectiveness = 0
                break
            elif ptype in type_chart[move_type]['weak']:
                effectiveness *= 2
            elif ptype in type_chart[move_type]['resist']:
                effectiveness *= 0.5
        
        return effectiveness
    
    def to_dict(self) -> Dict:
        """Convierte el Pokemon a diccionario"""
        return {
            'name': self.name,
            'species': self.species,
            'hp': self.hp,
            'max_hp': self.max_hp,
            'hp_percent': self.hp_percent,
            'level': self.level,
            'status': self.status.value,
            'moves': self.moves,
            'types': self.types,
            'fainted': self.fainted
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Pokemon':
        """Crea un Pokemon desde un diccionario"""
        status = Status.NONE
        if data.get('status'):
            try:
                status = Status(data['status'])
            except ValueError:
                status = Status.NONE
        
        return cls(
            name=data.get('name', 'Unknown'),
            species=data.get('species', ''),
            hp=data.get('hp', 100),
            max_hp=data.get('max_hp', 100),
            level=data.get('level', 100),
            status=status,
            moves=data.get('moves', []),
            types=data.get('types', []),
            fainted=data.get('fainted', False)
        )