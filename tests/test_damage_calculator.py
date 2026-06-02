"""
Pokemon Showdown Assistant - Tests para Damage Calculator
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.damage_calculator import DamageCalculator, SimpleDamageCalculator, DamageResult


class TestDamageCalculator(unittest.TestCase):
    """Tests para la calculadora de daño"""
    
    def setUp(self):
        self.calc = DamageCalculator()
    
    def test_effectiveness_no_effect(self):
        """Test efectividad neutra"""
        # Electric vs Normal (sin efecto)
        eff = self.calc.get_effectiveness('electric', ['normal'])
        self.assertEqual(eff, 1.0)
    
    def test_effectiveness_same_type(self):
        """Test efectividad del mismo tipo"""
        # Fire vs Fire (resistente)
        eff = self.calc.get_effectiveness('fire', ['fire'])
        self.assertEqual(eff, 0.5)
    
    def test_calculate_damage_basic(self):
        """Test cálculo básico de daño"""
        result = self.calc.calculate_damage(
            level=50,
            power=90,
            attack=100,
            defense=100,
            move_type='electric',
            defender_types=['normal'],
            stab=True,
            target_hp=100
        )
        
        self.assertIsInstance(result, DamageResult)
        self.assertGreater(result.min_damage, 0)
        self.assertGreater(result.max_damage, result.min_damage)
    
    def test_calculate_damage_with_stab(self):
        """Test STAB aumenta daño"""
        result_no_stab = self.calc.calculate_damage(
            level=50, power=90, attack=100, defense=100,
            move_type='electric', defender_types=['normal'],
            stab=False, target_hp=100
        )
        
        result_stab = self.calc.calculate_damage(
            level=50, power=90, attack=100, defense=100,
            move_type='electric', defender_types=['normal'],
            stab=True, target_hp=100
        )
        
        self.assertGreater(result_stab.max_damage, result_no_stab.max_damage)
    
    def test_calculate_damage_weather(self):
        """Test modificadores de clima"""
        result_normal = self.calc.calculate_damage(
            level=50, power=90, attack=100, defense=100,
            move_type='fire', defender_types=['grass'],
            stab=True, weather=None, target_hp=100
        )
        
        result_sun = self.calc.calculate_damage(
            level=50, power=90, attack=100, defense=100,
            move_type='fire', defender_types=['grass'],
            stab=True, weather='sun', target_hp=100
        )
        
        self.assertGreater(result_sun.max_damage, result_normal.max_damage)


class TestSimpleDamageCalculator(unittest.TestCase):
    """Tests para la calculadora simple"""
    
    def setUp(self):
        self.calc = SimpleDamageCalculator()
    
    def test_estimate_known_move(self):
        """Test estimación de movimientos conocidos"""
        power = self.calc.estimate('Thunderbolt')
        self.assertGreater(power, 0)
        
        power = self.calc.estimate('Surf')
        self.assertGreater(power, 0)
    
    def test_estimate_returns_value(self):
        """Test que siempre retorna un valor"""
        self.assertGreater(self.calc.estimate('anything'), 0)
    
    def test_estimate_consistency(self):
        """Test consistencia en estimaciones"""
        # Mismo movimiento debe dar mismo poder
        p1 = self.calc.estimate('Flamethrower')
        p2 = self.calc.estimate('flamethrower')
        self.assertEqual(p1, p2)


if __name__ == '__main__':
    unittest.main()