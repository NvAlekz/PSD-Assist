"""
Pokemon Showdown Assistant - Error Handler Middleware
Manejo centralizado de errores para toda la aplicación
"""

from typing import Callable, Any, Optional, Dict
from functools import wraps
from dataclasses import dataclass
from datetime import datetime
import traceback


@dataclass
class ErrorReport:
    """Reporte estructurado de un error"""
    error_type: str
    message: str
    timestamp: datetime
    context: Dict[str, Any]
    stack_trace: str
    resolved: bool = False


class ErrorHandler:
    """
    Manejador centralizado de errores
    
    Proporciona:
    - Captura y registro de errores
    - Categorización de errores
    - Fallbacks para operaciones críticas
    - Recovery strategies
    """
    
    def __init__(self):
        self.error_history: list[ErrorReport] = []
        self.max_history = 100
        self.fallbacks: Dict[str, Callable] = {}
    
    def register_fallback(self, operation: str, fallback: Callable):
        """Registra un fallback para una operación"""
        self.fallbacks[operation] = fallback
    
    def handle(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        operation: Optional[str] = None
    ) -> Any:
        """
        Maneja un error, intentando fallback si existe
        
        Returns:
            Resultado del fallback o None
        """
        report = ErrorReport(
            error_type=type(error).__name__,
            message=str(error),
            timestamp=datetime.now(),
            context=context or {},
            stack_trace=traceback.format_exc()
        )
        
        self.error_history.append(report)
        
        # Limitar historial
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)
        
        # Intentar fallback
        if operation and operation in self.fallbacks:
            try:
                return self.fallbacks[operation](error, context)
            except Exception as e:
                # Fallback también falló
                self.handle(e, {'fallback_failed': True}, operation)
        
        return None
    
    def wrap_operation(self, operation_name: str):
        """Decorador para envolver operaciones con manejo de errores"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    result = self.handle(e, {
                        'function': func.__name__,
                        'args': str(args)[:100],
                        'kwargs': str(kwargs)[:100]
                    }, operation_name)
                    
                    if operation_name in self.fallbacks:
                        return result
                    raise
            
            return wrapper
        return decorator
    
    def categorize_error(self, error: Exception) -> str:
        """Categoriza un error"""
        error_name = type(error).__name__
        
        categories = {
            'ValueError': 'validation',
            'TypeError': 'type_mismatch',
            'KeyError': 'missing_data',
            'IndexError': 'out_of_bounds',
            'AttributeError': 'invalid_object',
            'IOError': 'io_failure',
            'ConnectionError': 'network_failure',
            'TimeoutError': 'timeout'
        }
        
        return categories.get(error_name, 'unknown')
    
    def get_recent_errors(self, limit: int = 10) -> list[ErrorReport]:
        """Obtiene los errores más recientes"""
        return self.error_history[-limit:]
    
    def get_error_stats(self) -> Dict:
        """Obtiene estadísticas de errores"""
        categories = {}
        for err in self.error_history:
            cat = self.categorize_error(Exception(err.message))
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            'total_errors': len(self.error_history),
            'by_category': categories,
            'last_error': self.error_history[-1] if self.error_history else None
        }
    
    def mark_resolved(self, index: int):
        """Marca un error como resuelto"""
        if 0 <= index < len(self.error_history):
            self.error_history[index].resolved = True
    
    def clear_history(self):
        """Limpia el historial de errores"""
        self.error_history.clear()


# Instancia global
_global_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Obtiene la instancia global del manejador de errores"""
    global _global_handler
    if _global_handler is None:
        _global_handler = ErrorHandler()
    return _global_handler


def handle_errors(operation: Optional[str] = None):
    """Decorador para manejo automático de errores"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            handler = get_error_handler()
            try:
                return func(*args, **kwargs)
            except Exception as e:
                result = handler.handle(e, {
                    'function': func.__name__
                }, operation)
                
                if operation and operation in handler.fallbacks:
                    return result
                raise
        
        return wrapper
    return decorator


def with_fallback(operation: str, fallback: Any):
    """Decorador que especifica fallback para una operación"""
    handler = get_error_handler()
    handler.register_fallback(operation, fallback)
    
    def decorator(func: Callable) -> Callable:
        return handler.wrap_operation(operation)(func)
    
    return decorator