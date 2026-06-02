"""
Pokemon Showdown Assistant - Tests para Error Handler
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.error_handler import ErrorHandler, get_error_handler, handle_errors


class TestErrorHandler(unittest.TestCase):
    """Tests para el manejador de errores"""
    
    def setUp(self):
        self.handler = ErrorHandler()
    
    def test_handle_error(self):
        """Test manejo de errores básico"""
        error = ValueError("Test error")
        result = self.handler.handle(error, {'context': 'test'})
        
        self.assertEqual(len(self.handler.error_history), 1)
        self.assertEqual(self.handler.error_history[0].error_type, 'ValueError')
    
    def test_register_fallback(self):
        """Test registro de fallback"""
        def my_fallback(error, context):
            return "fallback_result"
        
        self.handler.register_fallback('test_operation', my_fallback)
        
        error = ValueError("Test")
        result = self.handler.handle(error, {}, 'test_operation')
        
        self.assertEqual(result, "fallback_result")
    
    def test_categorize_error(self):
        """Test categorización de errores"""
        # Verificar que devuelve categorías válidas
        self.assertEqual(self.handler.categorize_error(ValueError()), 'validation')
        self.assertEqual(self.handler.categorize_error(TypeError()), 'type_mismatch')
        self.assertEqual(self.handler.categorize_error(KeyError()), 'missing_data')
    
    def test_get_recent_errors(self):
        """Test obtener errores recientes"""
        for i in range(15):
            self.handler.handle(ValueError(f"Error {i}"), {})
        
        recent = self.handler.get_recent_errors(10)
        
        self.assertEqual(len(recent), 10)
    
    def test_get_error_stats(self):
        """Test estadísticas de errores"""
        # El categorize_error crea una nueva exception para categorizar
        # necesitamos verificar que funcione con los tipos reales
        self.handler.handle(ValueError("test1"), {})
        self.handler.handle(TypeError("test2"), {})
        self.handler.handle(IOError("test3"), {})
        
        stats = self.handler.get_error_stats()
        
        self.assertEqual(stats['total_errors'], 3)
        # Verificar que hay categorías
        self.assertGreater(len(stats['by_category']), 0)
        self.assertIsNotNone(stats['last_error'])
    
    def test_mark_resolved(self):
        """Test marcar error como resuelto"""
        self.handler.handle(ValueError("test"), {})
        
        self.assertFalse(self.handler.error_history[0].resolved)
        
        self.handler.mark_resolved(0)
        
        self.assertTrue(self.handler.error_history[0].resolved)
    
    def test_clear_history(self):
        """Test limpiar historial"""
        self.handler.handle(ValueError("test"), {})
        self.assertEqual(len(self.handler.error_history), 1)
        
        self.handler.clear_history()
        
        self.assertEqual(len(self.handler.error_history), 0)
    
    def test_global_handler(self):
        """Test handler global singleton"""
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        
        self.assertEqual(handler1, handler2)
    
    def test_decorator_handle_errors(self):
        """Test decorador handle_errors registra errores"""
        @handle_errors('test_op')
        def failing_function():
            raise ValueError("Test")
        
        # El decorador debe registrar el error
        # Puede relanzar si no hay fallback configurado
        try:
            failing_function()
        except ValueError:
            pass  # Esperado si no hay fallback
        
        # Verificar que se registró el error
        self.assertGreater(len(get_error_handler().error_history), 0)


class TestFallback(unittest.TestCase):
    """Tests para sistema de fallbacks"""
    
    def test_fallback_executed_on_error(self):
        """Test que el fallback se ejecuta cuando hay error"""
        handler = ErrorHandler()
        
        def my_fallback(error, context):
            return "recovered"
        
        handler.register_fallback('risky_op', my_fallback)
        
        def risky_operation():
            raise RuntimeError("Simulated failure")
        
        # Envolver con manejo de errores
        wrapped = handler.wrap_operation('risky_op')(risky_operation)
        
        result = wrapped()
        
        self.assertEqual(result, "recovered")
    
    def test_no_fallback_raises(self):
        """Test que sin fallback se lanza la excepción"""
        handler = ErrorHandler()
        
        def risky_operation():
            raise RuntimeError("Failure")
        
        wrapped = handler.wrap_operation('unknown_op')(risky_operation)
        
        with self.assertRaises(RuntimeError):
            wrapped()


if __name__ == '__main__':
    unittest.main()