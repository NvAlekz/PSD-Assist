"""
Pokemon Showdown Assistant - Tests para Win Condition Analyzer
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.win_condition_analyzer import WinConditionAnalyzer, WinCondition
from core.battle_state import BattleState, Pokemon, Team, Status


class TestWinConditionAnalyzer(unittest.TestCase):
    """Tests para el analizador de win conditions"""
    
    def setUp(self):
        self.analyzer = WinConditionAnalyzer()
    
    def test_analyze_ko_advantage(self):
        """Test análisis de ventaja de KO"""
        state = BattleState()
        state.my_team.add_pokemon(Pokemon(name='Pikachu', hp=100))
        state.my_team.add_pokemon(Pokemon(name='Charizard', hp=100))
        state.enemy_team.add_pokemon(Pokemon(name='Gengar', hp=0, fainted=True))
        
        conditions = self.analyzer.analyze(state)
        
        ko_conditions = [c for c in conditions if c.type == 'ko']
        self.assertGreater(len(ko_conditions), 0)
        # Ventaja de 2 Pokemon (2 vivos - 0 vivos enemigos = 2)
        self.assertIn('2', ko_conditions[0].description)
    
    def test_analyze_hp_advantage(self):
        """Test análisis de ventaja de HP"""
        state = BattleState()
        state.my_team.add_pokemon(Pokemon(name='Pikachu', hp=100))
        state.enemy_team.add_pokemon(Pokemon(name='Gengar', hp=50))
        
        conditions = self.analyzer.analyze(state)
        
        hp_conditions = [c for c in conditions if c.type == 'hp']
        self.assertGreater(len(hp_conditions), 0)
    
    def test_analyze_status_conditions(self):
        """Test análisis de condiciones de estado"""
        state = BattleState()
        
        # Mi Pokemon tiene enemigo quemado
        my_pkm = Pokemon(name='Pikachu', hp=100)
        enemy_pkm = Pokemon(name='Gengar', hp=50, status=Status.BURNED)
        
        state.my_team.add_pokemon(my_pkm)
        state.enemy_team.add_pokemon(enemy_pkm)
        
        conditions = self.analyzer.analyze(state)
        
        status_conditions = [c for c in conditions if c.type == 'status']
        self.assertGreater(len(status_conditions), 0)
    
    def test_analyze_hazards(self):
        """Test análisis de hazards"""
        state = BattleState()
        state.my_team.add_pokemon(Pokemon(name='Pikachu', hp=100))
        state.enemy_team.add_pokemon(Pokemon(name='Gengar', hp=100))
        
        state.enemy_hazards.spikes = 2
        
        conditions = self.analyzer.analyze(state)
        
        hazard_conditions = [c for c in conditions if c.type == 'hazard']
        self.assertGreater(len(hazard_conditions), 0)
        self.assertIn('2', hazard_conditions[0].description)
    
    def test_analyze_sweep_potential(self):
        """Test análisis de potencial de sweep"""
        state = BattleState()
        state.my_team.add_pokemon(Pokemon(name='Pikachu', hp=100))  # HP 100%
        state.enemy_team.add_pokemon(Pokemon(name='Gengar', hp=20))  # HP bajo
        
        conditions = self.analyzer.analyze(state)
        
        sweep_conditions = [c for c in conditions if c.type == 'sweep']
        self.assertGreater(len(sweep_conditions), 0)
    
    def test_estimate_hazard_damage(self):
        """Test estimación de daño por hazard"""
        self.assertEqual(self.analyzer.estimate_hazard_damage(1), 12)
        self.assertEqual(self.analyzer.estimate_hazard_damage(3), 25)
        self.assertEqual(self.analyzer.estimate_hazard_damage(4), 25)
    
    def test_get_win_probability(self):
        """Test cálculo de probabilidad de victoria"""
        state = BattleState()
        state.my_team.add_pokemon(Pokemon(name='Pikachu', hp=100))
        state.enemy_team.add_pokemon(Pokemon(name='Gengar', hp=20))
        
        prob = self.analyzer.get_win_probability(state)
        
        self.assertGreater(prob, 0.5)
        self.assertLessEqual(prob, 0.9)
    
    def test_suggest_next_action(self):
        """Test sugerencia de siguiente acción"""
        state = BattleState()
        state.my_team.add_pokemon(Pokemon(name='Pikachu', hp=100))
        state.enemy_team.add_pokemon(Pokemon(name='Gengar', hp=50))
        
        suggestion = self.analyzer.suggest_next_action(state)
        
        self.assertIn('action', suggestion)
        self.assertIn('reason', suggestion)
        self.assertIn(suggestion['action'], ['attack', 'status', 'hazard', 'switch'])
    
    def test_no_conditions_returns_default(self):
        """Test sin condiciones retorna默认值"""
        state = BattleState()
        
        # Sin Pokemon en ningún equipo
        prob = self.analyzer.get_win_probability(state)
        
        self.assertEqual(prob, 0.5)
    
    def test_conditions_sorted_by_priority(self):
        """Test que condiciones están ordenadas"""
        state = BattleState()
        state.my_team.add_pokemon(Pokemon(name='P1', hp=100))
        state.my_team.add_pokemon(Pokemon(name='P2', hp=100))
        state.enemy_team.add_pokemon(Pokemon(name='E1', hp=100))
        state.enemy_team.add_pokemon(Pokemon(name='E2', hp=100))
        
        conditions = self.analyzer.analyze(state)
        
        if len(conditions) > 1:
            # Verificar orden
            for i in range(len(conditions) - 1):
                self.assertGreaterEqual(
                    conditions[i].probability * conditions[i].priority,
                    conditions[i + 1].probability * conditions[i + 1].priority
                )


if __name__ == '__main__':
    unittest.main()