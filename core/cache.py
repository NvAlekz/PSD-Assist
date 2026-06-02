"""
Pokemon Showdown Assistant - Cache Module
Sistema de cache para datos frecuentemente accedidos
"""

from typing import Any, Callable, Optional, Dict, TypeVar
from functools import wraps
from datetime import datetime, timedelta
from dataclasses import dataclass
import hashlib
import json


T = TypeVar('T')


@dataclass
class CacheEntry:
    """Entrada individual del cache"""
    value: Any
    timestamp: datetime
    hits: int = 0
    ttl_seconds: Optional[int] = None
    
    def is_expired(self) -> bool:
        """Verifica si la entrada ha expirado"""
        if self.ttl_seconds is None:
            return False
        age = (datetime.now() - self.timestamp).total_seconds()
        return age > self.ttl_seconds
    
    def touch(self):
        """Actualiza el timestamp y contador de hits"""
        self.timestamp = datetime.now()
        self.hits += 1


class Cache:
    """
    Cache en memoria con TTL y políticas de eviction
    
    Características:
    - TTL configurable por entrada
    - Contador de hits para LRU
    - Maximum size con eviction
    - Serialización para persistencia opcional
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: Optional[int] = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl  # segundos
        self._cache: Dict[str, CacheEntry] = {}
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor del cache"""
        if key not in self._cache:
            self.stats['misses'] += 1
            return None
        
        entry = self._cache[key]
        
        # Verificar expiración
        if entry.is_expired():
            del self._cache[key]
            self.stats['misses'] += 1
            return None
        
        # Actualizar stats
        entry.touch()
        self.stats['hits'] += 1
        
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Establece un valor en el cache"""
        # Si estamos al máximo, evict LRU
        if len(self._cache) >= self.max_size and key not in self._cache:
            self._evict_lru()
        
        ttl = ttl if ttl is not None else self.default_ttl
        
        self._cache[key] = CacheEntry(
            value=value,
            timestamp=datetime.now(),
            ttl_seconds=ttl
        )
    
    def delete(self, key: str) -> bool:
        """Elimina una entrada del cache"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self):
        """Limpia todo el cache"""
        self._cache.clear()
    
    def _evict_lru(self):
        """Evict la entrada menos recientemente usada"""
        if not self._cache:
            return
        
        # Encontrar la entrada con menos hits
        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].hits)
        del self._cache[lru_key]
        self.stats['evictions'] += 1
    
    def cleanup_expired(self):
        """Limpia entradas expiradas"""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del cache"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'evictions': self.stats['evictions'],
            'hit_rate': f"{hit_rate:.2f}%"
        }
    
    def to_dict(self) -> Dict:
        """Serializa el cache para persistencia"""
        return {
            'max_size': self.max_size,
            'default_ttl': self.default_ttl,
            'entries': {
                k: {
                    'value': v.value,
                    'timestamp': v.timestamp.isoformat(),
                    'hits': v.hits,
                    'ttl_seconds': v.ttl_seconds
                }
                for k, v in self._cache.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Cache':
        """Crea un cache desde datos serializados"""
        cache = cls(max_size=data.get('max_size', 1000), default_ttl=data.get('default_ttl'))
        
        for key, entry_data in data.get('entries', {}).items():
            entry = CacheEntry(
                value=entry_data['value'],
                timestamp=datetime.fromisoformat(entry_data['timestamp']),
                hits=entry_data.get('hits', 0),
                ttl_seconds=entry_data.get('ttl_seconds')
            )
            # No restaurar entradas expiradas
            if not entry.is_expired():
                cache._cache[key] = entry
        
        return cache


def cached(ttl: Optional[int] = 300, key_prefix: str = ''):
    """
    Decorador para cachear resultados de funciones
    
    Args:
        ttl: Time-to-live en segundos
        key_prefix: Prefijo para la clave del cache
    """
    _cache = Cache()
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Generar clave única
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = hashlib.md5('|'.join(key_parts).encode()).hexdigest()
            
            # Intentar obtener del cache
            cached_value = _cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Ejecutar función y cachear resultado
            result = func(*args, **kwargs)
            _cache.set(cache_key, result, ttl)
            
            return result
        
        # Exponer cache para debugging
        wrapper._cache = _cache
        return wrapper
    
    return decorator


# Instancia global para uso compartido
_global_cache: Optional[Cache] = None


def get_cache() -> Cache:
    """Obtiene la instancia global del cache"""
    global _global_cache
    if _global_cache is None:
        _global_cache = Cache()
    return _global_cache


def invalidate_cache(key: str):
    """Invalida una entrada específica del cache global"""
    get_cache().delete(key)


def clear_cache():
    """Limpia el cache global"""
    get_cache().clear()