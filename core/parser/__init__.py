"""
Pokemon Showdown Assistant - Parser Module
Parser para datos de batallas de Pokemon Showdown
"""

from typing import Dict, List, Optional, Any
from ..battle_state import BattleState, Pokemon, Team, Hazards
from ..battle_state.pokemon import Status


class ShowdownParser:
    """
    Parser para extraer estado de batallas desde datos del DOM o mensajes
    """
    
    # Mapeo de nombres de Pokemon a especies (simplificado)
    POKEMON_SPECIES_MAP = {
        'Pikachu': 'pikachu',
        'Charizard': 'charizard',
        'Blastoise': 'blastoise',
        'Venusaur': 'venusaur',
        'Snorlax': 'snorlax',
        'Mewtwo': 'mewtwo',
        'Gengar': 'gengar',
        'Eevee': 'eevee',
        'Alakazam': 'alakazam',
        'Gyarados': 'gyarados',
    }
    
    def __init__(self):
        self.last_state = None
    
    def parse_battle_data(self, data: Dict) -> Optional[BattleState]:
        """
        Parsea datos crudos de una batalla
        
        Args:
            data: Diccionario con datos del DOM o API
            
        Returns:
            BattleState poblado o None si no hay datos válidos
        """
        if not data:
            return None
        
        state = BattleState()
        
        # Parsear Pokemon aliado activo
        if 'myPokemon' in data and data['myPokemon']:
            my_pokemon = self.parse_pokemon(data['myPokemon'])
            state.my_team.add_pokemon(my_pokemon)
        
        # Parsear Pokemon enemigo activo
        if 'enemyPokemon' in data and data['enemyPokemon']:
            enemy_pokemon = self.parse_pokemon(data['enemyPokemon'])
            state.enemy_team.add_pokemon(enemy_pokemon)
        
        # Parsear equipo aliado completo
        if 'myTeam' in data:
            for pkm_data in data['myTeam']:
                pkm = self.parse_pokemon(pkm_data)
                # Evitar duplicados del activo
                if not any(p.name == pkm.name for p in state.my_team.pokemons):
                    state.my_team.add_pokemon(pkm)
        
        # Parsear equipo enemigo
        if 'enemyTeam' in data:
            for pkm_data in data['enemyTeam']:
                pkm = self.parse_pokemon(pkm_data)
                if not any(p.name == pkm.name for p in state.enemy_team.pokemons):
                    state.enemy_team.add_pokemon(pkm)
        
        # Parsear hazards
        if 'hazards' in data:
            state.my_hazards = Hazards.from_dict(data['hazards'])
        
        # Timestamp
        if 'timestamp' in data:
            state.timestamp = data['timestamp']
        
        self.last_state = state
        return state
    
    def parse_pokemon(self, data: Dict) -> Pokemon:
        """
        Parsea datos de un Pokemon
        
        Args:
            data: Diccionario con datos del Pokemon
            
        Returns:
            Pokemon con datos poblados
        """
        name = data.get('name', 'Unknown')
        
        # Determinar especie
        first_word = name.split(' ')[0]
        species = self.POKEMON_SPECIES_MAP.get(first_word, first_word.lower())
        
        # Parsear HP
        hp = data.get('hp', 100)
        max_hp = data.get('maxHp', data.get('max_hp', 100))
        
        # Parsear estado
        status = Status.NONE
        if 'status' in data and data['status']:
            status_str = data['status'].lower()
            try:
                status = Status(status_str)
            except ValueError:
                status = self.guess_status(status_str)
        
        # Parsear movimientos
        moves = []
        if 'moves' in data:
            moves = data['moves'] if isinstance(data['moves'], list) else []
        if 'availableMoves' in data:
            moves = [m['name'] for m in data['availableMoves']]
        
        # Determinar tipos desde datos o especie
        types = data.get('types', [self.get_default_type(species)])
        
        return Pokemon(
            name=name,
            species=species,
            hp=int(hp),
            max_hp=int(max_hp),
            status=status,
            moves=moves,
            types=types
        )
    
    def guess_status(self, status_str: str) -> Status:
        """Infiere el estado desde una cadena"""
        status_map = {
            'brn': Status.BURNED,
            'burn': Status.BURNED,
            'psn': Status.POISONED,
            'poison': Status.POISONED,
            'tox': Status.TOXIC,
            'toxic': Status.TOXIC,
            'slp': Status.SLEEP,
            'sleep': Status.SLEEP,
            'frz': Status.FROZEN,
            'freeze': Status.FROZEN,
            'par': Status.PARALYZED,
            'paralyze': Status.PARALYZED,
        }
        
        for key, status in status_map.items():
            if key in status_str.lower():
                return status
        
        return Status.NONE
    
    def get_default_type(self, species: str) -> str:
        """Obtiene el tipo primario default para una especie"""
        type_defaults = {
            'pikachu': 'electric',
            'charizard': 'fire',
            'blastoise': 'water',
            'venusaur': 'grass',
            'snorlax': 'normal',
            'mewtwo': 'psychic',
            'gengar': 'ghost',
            'eevee': 'normal',
            'alakazam': 'psychic',
            'gyarados': 'water',
        }
        return type_defaults.get(species.lower(), 'normal')
    
    def parse_battle_log(self, log_lines: List[str]) -> List[Dict]:
        """
        Parsea líneas de log de batalla
        
        Args:
            log_lines: Lista de líneas del log
            
        Returns:
            Lista de eventos parseados
        """
        events = []
        
        for line in log_lines:
            event = self.parse_log_line(line)
            if event:
                events.append(event)
        
        return events
    
    def parse_log_line(self, line: str) -> Optional[Dict]:
        """Parsea una línea individual del log"""
        # Formato típico: |turn|1 o |move|Pikachu|Thunderbolt|
        
        if line.startswith('|turn|'):
            turn_num = line.replace('|turn|', '').strip()
            return {'type': 'turn', 'number': int(turn_num)}
        
        if line.startswith('|move|'):
            parts = line.split('|')
            if len(parts) >= 4:
                return {
                    'type': 'move',
                    'pokemon': parts[2],
                    'move': parts[3]
                }
        
        if line.startswith('|switch|') or line.startswith('|drag|'):
            parts = line.split('|')
            if len(parts) >= 4:
                pokemon_data = parts[3]
                return {
                    'type': 'switch',
                    'pokemon': self.extract_pokemon_name(pokemon_data)
                }
        
        return None
    
    def extract_pokemon_name(self, raw: str) -> str:
        """Extrae nombre de Pokemon de datos crudos"""
        # Formato: Pikachu, L50 o Charizard-Mega
        name = raw.split(',')[0].split('-')[0]
        return name.strip()