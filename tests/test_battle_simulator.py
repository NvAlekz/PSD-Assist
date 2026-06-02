"""
Pokemon Showdown Assistant - Tests para Battle Simulator
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.battle_simulator import BattleSimulator, SimulationResult


class TestBattleSimulator(unittest.TestCase):
    """Tests para el simulador de batallas"""
    
    def setUp(self):
        self.simulator = BattleSimulator()
    
    def test_simulate_move_basic(self):
        """Test simulación básica de movimiento"""
        attacker = {'name': 'Pikachu', 'attack': 80, 'hp': 100}
        defender = {'name': 'Gengar', 'defense': 70, 'hp': 95}
        
        result = self.simulator.simulate_move(attacker, defender, 'Thunderbolt', iterations=20)
        
        self.assertIsInstance(result, SimulationResult)
        self.assertEqual(result.action, 'Thunderbolt')
        self.assertGreater(result.expected_damage, 0)
        self.assertGreaterEqual(result.win_probability, 0)
        self.assertLessEqual(result.win_probability, 1)
    
    def test_simulate_switch(self):
        """Test simulación de cambio"""
        new_pokemon = {'name': 'Charizard', 'hp': 120}
        enemy = {'name': 'Gengar', 'attack': 90, 'defense': 60}
        
        result = self.simulator.simulate_switch(new_pokemon, enemy, iterations=20)
        
        self.assertIsInstance(result, SimulationResult)
        self.assertIn('Charizard', result.action)
        self.assertGreater(result.win_probability, 0)
    
    def test_compare_actions(self):
        """Test comparación de acciones"""
        state = {
            'attacker': {'name': 'Pikachu', 'attack': 80, 'hp': 100},
            'defender': {'name': 'Gengar', 'defense': 70, 'hp': 95}
        }
        actions = ['Thunderbolt', 'Quick Attack', 'Thunder Wave']
        
        results = self.simulator.compare_actions(state, actions)
        
        self.assertEqual(len(results), 3)
        # Verificar que están ordenados
        for i in range(len(results) - 1):
            self.assertGreaterEqual(
                results[i].win_probability,
                results[i + 1].win_probability
            )
    
    def test_simulate_full_battle(self):
        """Test simulación de batalla completa"""
        player_team = [
            {'name': 'Pikachu', 'hp': 100},
            {'name': 'Charizard', 'hp': 120},
            {'name': 'Blastoise', 'hp': 130}
        ]
        enemy_team = [
            {'name': 'Gengar', 'hp': 95},
            {'name': 'Alakazam', 'hp': 90},
            {'name': 'Gyarados', 'hp': 140}
        ]
        
        result = self.simulator.simulate_full_battle(
            player_team,
            enemy_team,
            max_turns=30
        )
        
        self.assertIn('winner', result)
        self.assertIn('turns', result)
        self.assertIn(result['winner'], ['player', 'enemy'])
        self.assertLessEqual(result['turns'], 30)
    
    def test_next_alive(self):
        """Test encontrar siguiente Pokemon vivo"""
        hp_list = [0, 50, 0, 75, 0]
        
        # Desde índice 0, debería encontrar 1
        next_idx = self.simulator._next_alive(hp_list, 0)
        self.assertEqual(next_idx, 1)
        
        # Desde índice 1, debería encontrar 3
        next_idx = self.simulator._next_alive(hp_list, 1)
        self.assertEqual(next_idx, 3)
        
        # Desde índice 3, debería encontrar 1 (wrap around)
        next_idx = self.simulator._next_alive(hp_list, 3)
        self.assertEqual(next_idx, 1)
    
    def test_risk_calculation(self):
        """Test cálculo de riesgo"""
        attacker = {'attack': 100}
        defender = {'defense': 80, 'hp': 100}
        
        result = self.simulator.simulate_move(
            attacker, defender, 'Test Move', iterations=100
        )
        
        self.assertGreaterEqual(result.risk_level, 0)
        self.assertLessEqual(result.risk_level, 1)
    
    def test_get_recommendation(self):
        """Test obtener recomendación"""
        state = {
            'attacker': {'name': 'Pikachu', 'attack': 80, 'hp': 100},
            'defender': {'name': 'Gengar', 'defense': 70, 'hp': 95}
        }
        actions = ['Thunderbolt', 'Quick Attack']
        
        rec = self.simulator.get_recommendation(state, actions)
        
        self.assertIn('action', rec)
        self.assertIn('win_probability', rec)
        self.assertIn('risk', rec)
        self.assertIn(rec['risk'], ['Low', 'Medium', 'High'])
    
    def test_recommendation_empty_actions(self):
        """Test recomendación con acciones vacías"""
        rec = self.simulator.get_recommendation({}, [])
        
        self.assertEqual(rec['action'], 'pass')
        self.assertIn('reason', rec)


if __name__ == '__main__':
    unittest.main()