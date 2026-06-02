"""
Pokemon Showdown Assistant - Team Model
Representa un equipo de Pokemon
"""

from dataclasses import dataclass, field
from typing import List, Optional
from .pokemon import Pokemon


@dataclass
class Team:
    """
    Modelo de un equipo de Pokemon
    
    Attributes:
        pokemons: Lista de Pokemon en el equipo
        name: Nombre del equipo (jugador)
    """
    pokemons: List[Pokemon] = field(default_factory=list)
    name: str = "Unknown"
    
    def add_pokemon(self, pokemon: Pokemon) -> None:
        """Añade un Pokemon al equipo"""
        self.pokemons.append(pokemon)
    
    def get_active(self) -> Optional[Pokemon]:
        """Obtiene el Pokemon activo del equipo"""
        for pkm in self.pokemons:
            if not pkm.fainted:
                return pkm
        return None
    
    def get_available_switches(self) -> List[Pokemon]:
        """Obtiene Pokemon disponibles para cambio"""
        return [pkm for pkm in self.pokemons if pkm.can_switch()]
    
    def get_fainted(self) -> List[Pokemon]:
        """Obtiene Pokemon debilitados"""
        return [pkm for pkm in self.pokemons if pkm.fainted]
    
    @property
    def remaining_count(self) -> int:
        """Cantidad de Pokemon no debilitados"""
        return len(self.get_available_switches())
    
    @property
    def is_alive(self) -> bool:
        """Verifica si el equipo tiene al menos un Pokemon vivo"""
        return self.get_active() is not None
    
    def get_low_hp_pokemons(self, threshold: int = 25) -> List[Pokemon]:
        """Obtiene Pokemon con HP bajo"""
        return [pkm for pkm in self.pokemons if not pkm.fainted and pkm.hp_percent <= threshold]
    
    def to_dict(self) -> dict:
        """Convierte el equipo a diccionario"""
        return {
            'name': self.name,
            'pokemons': [p.to_dict() for p in self.pokemons],
            'remaining_count': self.remaining_count
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Team':
        """Crea un equipo desde un diccionario"""
        team = cls(name=data.get('name', 'Unknown'))
        for pkm_data in data.get('pokemons', []):
            team.add_pokemon(Pokemon.from_dict(pkm_data))
        return team