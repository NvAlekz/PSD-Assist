"""
Pokemon Showdown Assistant - Tests para Metagame Analyzer
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.metagame_analyzer import MetagameAnalyzer, PokemonStats


class TestMetagameAnalyzer(unittest.TestCase):
    """Tests para el analizador de metagame"""
    
    def setUp(self):
        self.analyzer = MetagameAnalyzer()
    
    def test_analyze_battle(self):
        """Test análisis de batalla"""
        battle_data = {
            'myTeam': {
                'pokemons': [
                    {'name': 'Pikachu', 'hp': 80, 'maxHp': 100, 'moves': ['Thunderbolt']},
                    {'name': 'Charizard', 'hp': 100, 'maxHp': 150, 'moves': ['Flamethrower']}
                ]
            },
            'enemyTeam': {
                'pokemons': [
                    {'name': 'Gengar', 'hp': 0, 'maxHp': 95, 'moves': ['Shadow Ball']}
                ]
            },
            'winner': 'player'
        }
        
        self.analyzer.analyze_battle(battle_data)
        
        # Verificar que se analizaron Pokemon
        self.assertGreater(len(self.analyzer.pokemon_stats), 0)
        self.assertIn('Pikachu', self.analyzer.pokemon_stats)
    
    def test_get_top_pokemon(self):
        """Test obtener top Pokemon"""
        # Agregar datos manualmente
        self.analyzer.pokemon_stats['Pikachu'] = PokemonStats(name='Pikachu')
        self.analyzer.pokemon_stats['Pikachu'].usage_count = 10
        self.analyzer.pokemon_stats['Pikachu'].win_count = 7
        self.analyzer.pokemon_stats['Charizard'] = PokemonStats(name='Charizard')
        self.analyzer.pokemon_stats['Charizard'].usage_count = 5
        
        top = self.analyzer.get_top_pokemon(limit=5, by='usage')
        
        self.assertEqual(top[0].name, 'Pikachu')
        self.assertEqual(len(top) <= 5, True)
    
    def test_record_matchup(self):
        """Test registrar matchups"""
        self.analyzer.record_matchup('Pikachu', 'Gengar', won=True)
        self.analyzer.record_matchup('Pikachu', 'Gengar', won=True)
        self.analyzer.record_matchup('Pikachu', 'Gengar', won=False)
        
        key = ('Pikachu', 'Gengar')
        self.assertEqual(self.analyzer.matchups[key].wins, 2)
        self.assertEqual(self.analyzer.matchups[key].losses, 1)
    
    def test_win_rate_calculation(self):
        """Test cálculo de win rate"""
        stats = PokemonStats(name='Test')
        stats.usage_count = 10
        stats.win_count = 7
        stats.lose_count = 3
        
        self.assertEqual(stats.win_rate, 70.0)
    
    def test_get_matchup_advantage(self):
        """Test obtener ventaja de matchup"""
        self.analyzer.record_matchup('Pikachu', 'Gengar', won=True)
        self.analyzer.record_matchup('Pikachu', 'Gengar', won=True)
        self.analyzer.record_matchup('Pikachu', 'Gengar', won=True)
        self.analyzer.record_matchup('Pikachu', 'Gengar', won=False)
        
        advantage = self.analyzer.get_matchup_advantage('Pikachu', 'Gengar')
        
        # 75% winrate = 25% ventaja
        self.assertEqual(advantage, 25.0)
    
    def test_suggest_counter(self):
        """Test sugerir counter"""
        # Pikachu tiene 75% winrate vs Gengar
        self.analyzer.record_matchup('Pikachu', 'Gengar', won=True)
        self.analyzer.record_matchup('Pikachu', 'Gengar', won=True)
        self.analyzer.record_matchup('Pikachu', 'Gengar', won=True)
        self.analyzer.record_matchup('Pikachu', 'Gengar', won=False)
        
        # Mewtwo tiene 100% winrate vs Gengar
        self.analyzer.record_matchup('Mewtwo', 'Gengar', won=True)
        self.analyzer.record_matchup('Mewtwo', 'Gengar', won=True)
        
        counter = self.analyzer.suggest_counter('Gengar')
        
        # Mewtwo debería ser sugerido por tener mejor winrate
        self.assertEqual(counter, 'Mewtwo')
    
    def test_reset(self):
        """Test reset de estadísticas"""
        self.analyzer.pokemon_stats['Pikachu'] = PokemonStats(name='Pikachu')
        self.analyzer.pokemon_stats['Pikachu'].usage_count = 10
        self.analyzer.record_matchup('Pikachu', 'Gengar', won=True)
        
        self.analyzer.reset()
        
        self.assertEqual(len(self.analyzer.pokemon_stats), 0)
        self.assertEqual(len(self.analyzer.matchups), 0)
    
    def test_export_to_dict(self):
        """Test exportación de datos"""
        self.analyzer.pokemon_stats['Pikachu'] = PokemonStats(name='Pikachu')
        self.analyzer.pokemon_stats['Pikachu'].usage_count = 5
        self.analyzer.pokemon_stats['Pikachu'].win_count = 3
        
        data = self.analyzer.export_to_dict()
        
        self.assertIn('pokemon_stats', data)
        self.assertIn('Pikachu', data['pokemon_stats'])
        self.assertEqual(data['pokemon_stats']['Pikachu']['usage_count'], 5)


if __name__ == '__main__':
    unittest.main()