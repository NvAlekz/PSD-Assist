"""
Pokemon Showdown Assistant - Tests de Integración
Tests que validan la interacción entre módulos
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.battle_state import Pokemon, Team, BattleState, Status, Hazards
from core.parser import ShowdownParser
from core.recommendation_engine import RecommendationEngine
from core.storage import BattleStorage


class TestIntegration(unittest.TestCase):
    """Tests de integración entre módulos"""
    
    def setUp(self):
        self.parser = ShowdownParser()
        self.engine = RecommendationEngine()
        self.storage = BattleStorage('data/test_battles')
    
    def test_parse_to_battle_state(self):
        """Test integración parser -> BattleState"""
        # Simular datos del DOM
        raw_data = {
            'myPokemon': {
                'name': 'Pikachu',
                'hp': 85,
                'maxHp': 100,
                'status': 'paralyzed',
                'moves': ['Thunderbolt', 'Quick Attack']
            },
            'enemyPokemon': {
                'name': 'Gengar',
                'hp': 60,
                'maxHp': 95,
                'status': None,
                'moves': ['Shadow Ball', 'Focus Blast']
            },
            'myTeam': [
                {'name': 'Pikachu', 'hp': 85, 'maxHp': 100},
                {'name': 'Charizard', 'hp': 120, 'maxHp': 150}
            ],
            'hazards': {
                'spikes': 1,
                'stealthRock': False
            }
        }
        
        # Parsear
        state = self.parser.parse_battle_data(raw_data)
        
        # Verificar integración
        self.assertIsNotNone(state)
        self.assertEqual(state.my_active.name, 'Pikachu')
        self.assertEqual(state.my_active.hp, 85)
        self.assertEqual(state.enemy_active.name, 'Gengar')
        self.assertEqual(state.my_hazards.spikes, 1)
        self.assertEqual(len(state.my_team.pokemons), 2)
    
    def test_battle_state_to_engine(self):
        """Test integración BattleState -> RecommendationEngine"""
        state = BattleState()
        state.my_team.add_pokemon(Pokemon(
            name="Blastoise",
            hp=100,
            max_hp=150,
            types=['water'],
            moves=['Surf', 'Ice Beam', 'Rapid Spin', 'Protect']
        ))
        state.enemy_team.add_pokemon(Pokemon(
            name="Charizard",
            hp=80,
            max_hp=120,
            types=['fire', 'flying'],
            moves=['Flamethrower', 'Air Slash', 'Dragon Claw']
        ))
        
        # Obtener recomendaciones
        recommendations = self.engine.get_recommendations(state)
        
        # Verificar que el engine usó correctamente los datos del estado
        self.assertGreater(len(recommendations), 0)
        self.assertTrue(any('Surf' in r.move or 'Ice' in r.move for r in recommendations))
    
    def test_state_serialization_cycle(self):
        """Test ciclo completo: crear -> serializar -> deserializar"""
        original_state = BattleState()
        original_state.turn = 5
        original_state.my_team.add_pokemon(Pokemon(
            name="Snorlax",
            hp=200,
            max_hp=250,
            status=Status.BURNED,
            types=['normal']
        ))
        original_state.enemy_team.add_pokemon(Pokemon(
            name="Machamp",
            hp=150,
            max_hp=180,
            types=['fighting']
        ))
        original_state.my_hazards.spikes = 2
        
        # Serializar
        data = original_state.to_dict()
        
        # Deserializar
        restored_state = BattleState.from_dict(data)
        
        # Verificar integridad
        self.assertEqual(restored_state.turn, 5)
        self.assertEqual(len(restored_state.my_team.pokemons), 1)
        self.assertEqual(restored_state.my_team.pokemons[0].name, 'Snorlax')
        self.assertEqual(restored_state.my_team.pokemons[0].hp, 200)
        self.assertEqual(restored_state.my_team.pokemons[0].status, Status.BURNED)
        self.assertEqual(restored_state.my_hazards.spikes, 2)
    
    def test_full_recommendation_pipeline(self):
        """Test pipeline completo: datos -> parser -> engine -> recomendación"""
        # Simular datos de entrada
        input_data = {
            'myPokemon': {
                'name': 'Venusaur',
                'hp': 100,
                'maxHp': 120,
                'moves': ['Giga Drain', 'Sludge Bomb', 'Earthquake', 'Synthesis']
            },
            'enemyPokemon': {
                'name': 'Blastoise',
                'hp': 90,
                'maxHp': 130,
                'moves': ['Hydro Pump', 'Ice Beam', 'Rapid Spin']
            }
        }
        
        # Pipeline
        state = self.parser.parse_battle_data(input_data)
        recommendations = self.engine.get_recommendations(state, max_results=3)
        
        # Verificar resultados
        self.assertEqual(len(recommendations), 3)
        
        # Primera recomendación debe ser Earthquake (superefectivo vs Blastoise)
        # o Giga Drain (neutral pero recovery)
        self.assertTrue(recommendations[0].priority == 1)
        self.assertIsNotNone(recommendations[0].move)
    
    def test_storage_save_load_cycle(self):
        """Test guardar y cargar batalla"""
        state = BattleState()
        state.turn = 10
        state.battle_id = "test_battle_001"
        state.my_team.add_pokemon(Pokemon(
            name="Alakazam",
            hp=80,
            max_hp=90
        ))
        
        # Guardar
        filepath = self.storage.save_battle(state)
        self.assertTrue(os.path.exists(filepath))
        
        # Cargar
        loaded_state = self.storage.load_battle("test_battle_001")
        
        # Verificar
        self.assertIsNotNone(loaded_state)
        self.assertEqual(loaded_state.turn, 10)
        self.assertEqual(loaded_state.battle_id, "test_battle_001")
        self.assertEqual(loaded_state.my_team.pokemons[0].name, "Alakazam")
        
        # Limpiar
        os.remove(filepath)
        os.rmdir(self.storage.storage_dir)
    
    def test_type_effectiveness_in_recommendation(self):
        """Test que la efectividad de tipos afecta las recomendaciones"""
        state = BattleState()
        
        # Water vs Fire (no muy efectivo)
        state.my_team.add_pokemon(Pokemon(
            name="Golduck",
            hp=100,
            types=['water'],
            moves=['Surf', 'Psychic']
        ))
        state.enemy_team.add_pokemon(Pokemon(
            name="Arcanine",
            hp=100,
            types=['fire'],
            moves=['Flamethrower']
        ))
        
        recs = self.engine.get_recommendations(state)
        
        # Buscar Psychic (superefectivo vs Fire) vs Surf
        psych_rec = next((r for r in recs if 'Psychic' in r.move), None)
        surf_rec = next((r for r in recs if 'Surf' in r.move), None)
        
        # Psychic debería tener mayor score que Surf
        if psych_rec and surf_rec:
            self.assertGreater(psych_rec.score, surf_rec.score)


class TestRecommendationEngineIntegration(unittest.TestCase):
    """Tests específicos para el motor de recomendación"""
    
    def setUp(self):
        self.engine = RecommendationEngine()
    
    def test_recommend_when_hp_low(self):
        """Test recomendaciones cuando HP está bajo"""
        state = BattleState()
        state.my_team.add_pokemon(Pokemon(
            name="Gengar",
            hp=15,  # HP muy bajo
            max_hp=95,
            moves=['Shadow Ball', 'Focus Blast']
        ))
        state.enemy_team.add_pokemon(Pokemon(
            name="Gengar",
            hp=80,
            types=['ghost', 'poison']
        ))
        
        # Agregar Pokemon de respaldo
        state.my_team.add_pokemon(Pokemon(
            name="Alakazam",
            hp=100,
            types=['psychic']
        ))
        
        recs = self.engine.get_recommendations(state)
        
        # Debería recomendar cambio
        switch_recs = [r for r in recs if 'Cambiar' in r.move]
        self.assertGreater(len(switch_recs), 0)
        
        # Los cambios deben estar rankeados
        self.assertTrue(all(r.priority > 0 for r in recs))
    
    def test_recommend_super_effective(self):
        """Test que recomienda movimientos superefectivos"""
        state = BattleState()
        state.my_team.add_pokemon(Pokemon(
            name="Vulpix",
            hp=100,
            types=['fire'],
            moves=['Ember', 'Confuse Ray', 'Fire Spin']
        ))
        state.enemy_team.add_pokemon(Pokemon(
            name="Bulbasaur",
            hp=100,
            types=['grass', 'poison']
        ))
        
        recs = self.engine.get_recommendations(state)
        
        # Ember debería estar entre las primeras recomendaciones
        ember_rec = next((r for r in recs if 'Ember' in r.move), None)
        
        self.assertIsNotNone(ember_rec)
        # Debería tener razón de superefectividad
        self.assertTrue('superefectivo' in ember_rec.reason.lower() or 
                       'fire' in ember_rec.reason.lower() or
                       ember_rec.score > 20)


if __name__ == '__main__':
    unittest.main()