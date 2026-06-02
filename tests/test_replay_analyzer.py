"""
Pokemon Showdown Assistant - Tests para Replay Analyzer
"""

import unittest
import sys
import os
import tempfile
import shutil
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.replay_analyzer import ReplayAnalyzer, ReplayAnalysis


class TestReplayAnalyzer(unittest.TestCase):
    """Tests para el analizador de replays"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.analyzer = ReplayAnalyzer(self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_analyze_replay_data(self):
        """Test análisis de datos de replay"""
        data = {
            'id': 'test_001',
            'winner': 'player',
            'turn': 15,
            'player_team': ['Pikachu', 'Charizard', 'Blastoise'],
            'enemy_team': ['Gengar', 'Alakazam', 'Gyarados'],
            'history': [
                {'type': 'move', 'player': 'player', 'pokemon': 'Pikachu', 'move': 'Thunderbolt', 'result': 'hit'},
                {'type': 'move', 'player': 'enemy', 'pokemon': 'Gengar', 'move': 'Shadow Ball', 'result': 'hit'},
                {'type': 'switch', 'player': 'player', 'pokemon': 'Charizard'},
            ]
        }
        
        analysis = self.analyzer.analyze_replay_data(data)
        
        self.assertEqual(analysis.replay_id, 'test_001')
        self.assertEqual(analysis.winner, 'player')
        self.assertEqual(analysis.duration_turns, 15)
        self.assertEqual(analysis.total_moves, 2)
        self.assertEqual(analysis.total_switches, 1)
    
    def test_detect_patterns(self):
        """Test detección de patrones"""
        history = [
            {'type': 'move', 'move': 'Thunderbolt', 'result': 'hit'},
            {'type': 'move', 'move': 'Thunderbolt', 'result': 'hit'},
            {'type': 'move', 'move': 'Thunderbolt', 'result': 'hit'},
            {'type': 'move', 'move': 'Thunderbolt', 'result': 'hit'},
            {'type': 'switch', 'player': 'player', 'pokemon': 'Charizard'},
        ]
        
        patterns = self.analyzer.detect_patterns(history)
        
        self.assertTrue(any('Thunderbolt 4' in p for p in patterns))
    
    def test_suggest_improvements_low_accuracy(self):
        """Test sugerencias con accuracy bajo"""
        analysis = ReplayAnalysis(
            replay_id='test',
            date=datetime.now(),
            winner='player',
            duration_turns=10,
            total_moves=10,
            accurate_moves=5,  # 50% accuracy
            ko_moves=0,
            super_effective_moves=1
        )
        
        improvements = self.analyzer.suggest_improvements(analysis)
        
        self.assertTrue(any('точность' in imp.lower() or 'accuracy' in imp.lower() for imp in improvements))
    
    def test_save_replay(self):
        """Test guardar replay"""
        battle_data = {
            'winner': 'player',
            'turn': 10,
            'player_team': ['Pikachu'],
            'enemy_team': ['Gengar'],
            'history': []
        }
        
        filepath = self.analyzer.save_replay(battle_data)
        
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(filepath.endswith('.json'))
    
    def test_load_replay(self):
        """Test cargar replay"""
        battle_data = {
            'id': 'load_test',
            'winner': 'enemy',
            'turn': 8,
            'player_team': ['Blastoise'],
            'enemy_team': ['Charizard'],
            'history': []
        }
        
        filepath = self.analyzer.save_replay(battle_data)
        loaded = self.analyzer.load_replay(filepath)
        
        self.assertIsNotNone(loaded)
        # El id puede ser reescrito por save_replay, verificar que cargó correctamente
        self.assertEqual(loaded.winner, 'enemy')
        self.assertEqual(loaded.duration_turns, 8)
    
    def test_get_win_rate_by_pokemon(self):
        """Test cálculo de win rate por Pokemon"""
        # Agregar algunos replays
        data1 = {
            'winner': 'player',
            'turn': 10,
            'player_team': ['Pikachu', 'Charizard'],
            'enemy_team': ['Gengar'],
            'history': []
        }
        data2 = {
            'winner': 'player',
            'turn': 12,
            'player_team': ['Pikachu', 'Blastoise'],
            'enemy_team': ['Gengar'],
            'history': []
        }
        data3 = {
            'winner': 'enemy',
            'turn': 9,
            'player_team': ['Pikachu', 'Snorlax'],
            'enemy_team': ['Gengar'],
            'history': []
        }
        
        self.analyzer.analyze_replay_data(data1)
        self.analyzer.analyze_replay_data(data2)
        self.analyzer.analyze_replay_data(data3)
        
        win_rates = self.analyzer.get_win_rate_by_pokemon()
        
        self.assertIn('Pikachu', win_rates)
        self.assertEqual(win_rates['Pikachu'], 2/3)  # 2 wins, 3 games
    
    def test_export_learning(self):
        """Test exportación de aprendizaje"""
        data = {
            'winner': 'player',
            'turn': 10,
            'player_team': ['Pikachu'],
            'enemy_team': ['Gengar'],
            'history': []
        }
        self.analyzer.analyze_replay_data(data)
        
        learning = self.analyzer.export_learning()
        
        self.assertIn('total_replays', learning)
        self.assertEqual(learning['total_replays'], 1)
        self.assertEqual(learning['player_winrate'], 1.0)


if __name__ == '__main__':
    unittest.main()