"""
Pokemon Showdown Assistant - Tests
Tests unitarios para el core del proyecto
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.battle_state.pokemon import Pokemon, Status
from core.battle_state.team import Team
from core.battle_state.battle_state import BattleState, Hazards
from core.parser import ShowdownParser
from core.recommendation_engine import RecommendationEngine


class TestPokemon(unittest.TestCase):
    """Tests para la clase Pokemon"""
    
    def test_pokemon_creation(self):
        """Test creación básica de Pokemon"""
        pkm = Pokemon(name="Pikachu", hp=80, max_hp=100)
        
        self.assertEqual(pkm.name, "Pikachu")
        self.assertEqual(pkm.hp, 80)
        self.assertEqual(pkm.max_hp, 100)
        self.assertFalse(pkm.fainted)
    
    def test_hp_percent(self):
        """Test cálculo de porcentaje de HP"""
        pkm = Pokemon(name="Pikachu", hp=50, max_hp=100)
        self.assertEqual(pkm.hp_percent, 50)
        
        pkm2 = Pokemon(name="Charizard", hp=150, max_hp=200)
        self.assertEqual(pkm2.hp_percent, 75)
    
    def test_hp_category(self):
        """Test categorías de HP"""
        pkm_high = Pokemon(name="Test", hp=75, max_hp=100)
        self.assertEqual(pkm_high.hp_category, "high")
        
        pkm_medium = Pokemon(name="Test", hp=35, max_hp=100)
        self.assertEqual(pkm_medium.hp_category, "medium")
        
        pkm_low = Pokemon(name="Test", hp=15, max_hp=100)
        self.assertEqual(pkm_low.hp_category, "low")
    
    def test_fainted_pokemon(self):
        """Test Pokemon debilitado"""
        pkm = Pokemon(name="Test", hp=0, max_hp=100)
        self.assertTrue(pkm.fainted)
    
    def test_type_effectiveness(self):
        """Test efectividad de tipos"""
        grass_pkm = Pokemon(name="Bulbasaur", types=['grass', 'poison'])
        
        # Verificar que los tipos están asignados
        self.assertEqual(len(grass_pkm.types), 2)
        
        # Fire es superefectivo contra Grass
        self.assertEqual(grass_pkm.get_type_effectiveness('fire'), 2.0)
        
        # Psychic es superefectivo contra Poison (2x)
        self.assertGreaterEqual(grass_pkm.get_type_effectiveness('psychic'), 1.0)
    
    def test_pokemon_to_dict(self):
        """Test serialización a diccionario"""
        pkm = Pokemon(
            name="Pikachu",
            species="pikachu",
            hp=80,
            max_hp=100,
            status=Status.PARALYZED
        )
        
        data = pkm.to_dict()
        
        self.assertEqual(data['name'], "Pikachu")
        self.assertEqual(data['hp'], 80)
        self.assertEqual(data['status'], 'paralyzed')
    
    def test_pokemon_from_dict(self):
        """Test deserialización desde diccionario"""
        data = {
            'name': 'Gengar',
            'species': 'gengar',
            'hp': 50,
            'max_hp': 100,
            'status': 'sleep',
            'fainted': False
        }
        
        pkm = Pokemon.from_dict(data)
        
        self.assertEqual(pkm.name, "Gengar")
        self.assertEqual(pkm.hp, 50)
        self.assertEqual(pkm.status, Status.SLEEP)


class TestTeam(unittest.TestCase):
    """Tests para la clase Team"""
    
    def test_team_creation(self):
        """Test creación de equipo"""
        team = Team(name="Player1")
        self.assertEqual(team.name, "Player1")
        self.assertEqual(len(team.pokemons), 0)
    
    def test_add_pokemon(self):
        """Test agregar Pokemon al equipo"""
        team = Team()
        pkm = Pokemon(name="Pikachu")
        
        team.add_pokemon(pkm)
        
        self.assertEqual(len(team.pokemons), 1)
        self.assertEqual(team.pokemons[0].name, "Pikachu")
    
    def test_get_active(self):
        """Test obtener Pokemon activo"""
        team = Team()
        team.add_pokemon(Pokemon(name="Pikachu", hp=50))
        team.add_pokemon(Pokemon(name="Gengar", hp=0))
        
        active = team.get_active()
        
        self.assertIsNotNone(active)
        self.assertEqual(active.name, "Pikachu")
    
    def test_get_available_switches(self):
        """Test obtener cambios disponibles"""
        team = Team()
        team.add_pokemon(Pokemon(name="Pikachu", hp=50))
        team.add_pokemon(Pokemon(name="Gengar", hp=0))
        team.add_pokemon(Pokemon(name="Charizard", hp=30))
        
        switches = team.get_available_switches()
        
        self.assertEqual(len(switches), 2)
    
    def test_remaining_count(self):
        """Test conteo de Pokemon restantes"""
        team = Team()
        team.add_pokemon(Pokemon(name="P1", hp=100))
        team.add_pokemon(Pokemon(name="P2", hp=0))
        team.add_pokemon(Pokemon(name="P3", hp=50))
        
        self.assertEqual(team.remaining_count, 2)


class TestBattleState(unittest.TestCase):
    """Tests para la clase BattleState"""
    
    def test_battle_state_creation(self):
        """Test creación de estado de batalla"""
        state = BattleState()
        
        self.assertEqual(state.turn, 0)
        self.assertIsNone(state.my_active)
        self.assertIsNone(state.enemy_active)
    
    def test_advance_turn(self):
        """Test avanzar turno"""
        state = BattleState()
        state.advance_turn()
        
        self.assertEqual(state.turn, 1)
        
        state.advance_turn()
        self.assertEqual(state.turn, 2)
    
    def test_is_battle_over(self):
        """Test determinar fin de batalla"""
        state = BattleState()
        
        # Ambos con HP
        state.my_team.add_pokemon(Pokemon(name="Test", hp=100))
        state.enemy_team.add_pokemon(Pokemon(name="Enemy", hp=100))
        
        # Battle no debería estar terminada
        self.assertFalse(state.is_battle_over)
        
        # Equipo aliado derrotado (todos con HP 0)
        state.my_team.pokemons[0].hp = 0
        state.my_team.pokemons[0].fainted = True
        
        # Ahora la batalla debería estar terminada
        self.assertTrue(state.is_battle_over)
    
    def test_hazards(self):
        """Test hazards"""
        hazards = Hazards(spikes=2, stealth_rock=True)
        
        self.assertEqual(hazards.spikes, 2)
        self.assertTrue(hazards.stealth_rock)
        
        data = hazards.to_dict()
        self.assertEqual(data['spikes'], 2)
        self.assertTrue(data['stealthRock'])


class TestShowdownParser(unittest.TestCase):
    """Tests para el parser"""
    
    def setUp(self):
        self.parser = ShowdownParser()
    
    def test_parse_pokemon_data(self):
        """Test parsear datos de Pokemon"""
        data = {
            'myPokemon': {
                'name': 'Pikachu',
                'hp': 80,
                'maxHp': 100,
                'status': 'paralyzed',
                'moves': ['Thunderbolt', 'Quick Attack']
            }
        }
        
        state = self.parser.parse_battle_data(data)
        
        self.assertIsNotNone(state)
        self.assertIsNotNone(state.my_active)
        self.assertEqual(state.my_active.name, 'Pikachu')
        self.assertEqual(state.my_active.hp, 80)
        self.assertEqual(state.my_active.status, Status.PARALYZED)
    
    def test_parse_team(self):
        """Test parsear equipo"""
        data = {
            'myTeam': [
                {'name': 'Pikachu', 'hp': 80, 'maxHp': 100},
                {'name': 'Charizard', 'hp': 100, 'maxHp': 150}
            ]
        }
        
        state = self.parser.parse_battle_data(data)
        
        self.assertEqual(len(state.my_team.pokemons), 2)
        self.assertEqual(state.my_team.pokemons[0].name, 'Pikachu')
        self.assertEqual(state.my_team.pokemons[1].name, 'Charizard')
    
    def test_parse_hazards(self):
        """Test parsear hazards"""
        data = {
            'hazards': {
                'spikes': 1,
                'toxicSpikes': 2,
                'stealthRock': True,
                'stickyWeb': False
            }
        }
        
        state = self.parser.parse_battle_data(data)
        
        self.assertEqual(state.my_hazards.spikes, 1)
        self.assertEqual(state.my_hazards.toxic_spikes, 2)
        self.assertTrue(state.my_hazards.stealth_rock)


class TestRecommendationEngine(unittest.TestCase):
    """Tests para el motor de recomendaciones"""
    
    def setUp(self):
        self.engine = RecommendationEngine()
        
        # Crear estado de batalla de prueba
        self.state = BattleState()
        self.state.my_team.add_pokemon(Pokemon(
            name="Pikachu",
            hp=100,
            max_hp=100,
            moves=["Thunderbolt", "Quick Attack", "Iron Tail", "Volt Tackle"]
        ))
        self.state.enemy_team.add_pokemon(Pokemon(
            name="Gengar",
            hp=80,
            max_hp=100,
            types=["ghost", "poison"]
        ))
    
    def test_get_recommendations(self):
        """Test obtener recomendaciones"""
        recs = self.engine.get_recommendations(self.state, max_results=3)
        
        self.assertLessEqual(len(recs), 3)
        
        # Verificar que hay recomendaciones
        self.assertGreater(len(recs), 0)
        
        # Verificar que están ordenadas por score
        if len(recs) > 1:
            self.assertGreaterEqual(recs[0].score, recs[1].score)
    
    def test_move_type_detection(self):
        """Test detección de tipo de movimiento"""
        self.assertEqual(self.engine.get_move_type("Thunderbolt"), "electric")
        self.assertEqual(self.engine.get_move_type("Flamethrower"), "fire")
        self.assertEqual(self.engine.get_move_type("Surf"), "water")
    
    def test_danger_calculation(self):
        """Test cálculo de peligro"""
        danger = self.engine.calculate_danger(
            self.state.my_active,
            self.state.enemy_active
        )
        
        self.assertGreaterEqual(danger, 0)
        self.assertLessEqual(danger, 100)


if __name__ == '__main__':
    unittest.main()