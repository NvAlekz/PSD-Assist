"""
Pokemon Showdown Assistant - Tests para Logging
"""

import unittest
import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.logging_config import BattleLogger, get_logger


class TestBattleLogger(unittest.TestCase):
    """Tests para el sistema de logging"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.logger = BattleLogger('test', self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_logger_creation(self):
        """Test creación de logger"""
        self.assertIsNotNone(self.logger)
        self.assertEqual(self.logger.name, 'test')
    
    def test_singleton_pattern(self):
        """Test patrón singleton"""
        logger1 = BattleLogger.get_instance(name='singleton_test')
        logger2 = BattleLogger.get_instance()
        
        self.assertEqual(logger1, logger2)
    
    def test_log_levels(self):
        """Test diferentes niveles de log"""
        # No debe lanzar excepciones
        self.logger.debug("Debug message")
        self.logger.info("Info message")
        self.logger.warning("Warning message")
        self.logger.error("Error message")
        self.logger.critical("Critical message")
    
    def test_format_message(self):
        """Test formateo de mensajes"""
        msg = self.logger._format_message("Test", key="value", num=42)
        
        self.assertIn("Test", msg)
        self.assertIn("key=value", msg)
        self.assertIn("num=42", msg)
    
    def test_log_battle_event(self):
        """Test log de eventos de batalla"""
        event_data = {
            'pokemon': 'Pikachu',
            'hp': 85,
            'turn': 5
        }
        
        # No debe lanzar excepciones
        self.logger.log_battle_event('DAMAGE', event_data)
    
    def test_log_recommendation(self):
        """Test log de recomendaciones"""
        rec = {
            'action': 'Thunderbolt',
            'score': 85.5,
            'reason': 'Superefectivo'
        }
        
        # No debe lanzar excepciones
        self.logger.log_recommendation(rec)
    
    def test_set_level(self):
        """Test cambiar nivel de logging"""
        self.logger.set_level('DEBUG')
        self.assertEqual(self.logger.logger.level, 10)  # DEBUG = 10
        
        self.logger.set_level('ERROR')
        self.assertEqual(self.logger.logger.level, 40)  # ERROR = 40
    
    def test_get_recent_logs(self):
        """Test obtener logs recientes"""
        # Generar algunos logs
        self.logger.info("Test log 1")
        self.logger.info("Test log 2")
        
        logs = self.logger.get_recent_logs(lines=10)
        
        self.assertIsInstance(logs, str)
    
    def test_get_logger_helper(self):
        """Test función helper get_logger"""
        logger = get_logger('helper_test', log_dir=self.temp_dir)
        
        self.assertIsInstance(logger, BattleLogger)
        self.assertEqual(logger.name, 'helper_test')


if __name__ == '__main__':
    unittest.main()