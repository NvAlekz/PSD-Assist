"""
Pokemon Showdown Assistant - Tests para Cache
"""

import unittest
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.cache import Cache, cached, get_cache, clear_cache


class TestCache(unittest.TestCase):
    """Tests para el sistema de cache"""
    
    def setUp(self):
        self.cache = Cache(max_size=10, default_ttl=60)
    
    def test_set_and_get(self):
        """Test básico de set/get"""
        self.cache.set('key1', 'value1')
        
        result = self.cache.get('key1')
        
        self.assertEqual(result, 'value1')
    
    def test_cache_miss(self):
        """Test cuando no existe la clave"""
        result = self.cache.get('nonexistent')
        
        self.assertIsNone(result)
    
    def test_delete(self):
        """Test eliminar entrada"""
        self.cache.set('key1', 'value1')
        
        deleted = self.cache.delete('key1')
        
        self.assertTrue(deleted)
        self.assertIsNone(self.cache.get('key1'))
    
    def test_ttl_expiration(self):
        """Test expiración por TTL"""
        cache = Cache(max_size=10, default_ttl=1)  # 1 segundo
        cache.set('key', 'value')
        
        # Inmediatamente debe existir
        self.assertEqual(cache.get('key'), 'value')
        
        # Después de 2 segundos debe expirar
        time.sleep(2)
        
        self.assertIsNone(cache.get('key'))
    
    def test_lru_eviction(self):
        """Test evict LRU cuando está lleno"""
        cache = Cache(max_size=3)
        
        cache.set('a', 1)
        cache.set('b', 2)
        cache.set('c', 3)
        
        # Agregar第四次, debe evict el menos usado (a)
        cache.set('d', 4)
        
        self.assertIsNone(cache.get('a'))
        self.assertEqual(cache.get('d'), 4)
    
    def test_stats(self):
        """Test estadísticas del cache"""
        self.cache.set('key1', 'value1')
        self.cache.get('key1')  # hit
        self.cache.get('key1')  # hit
        self.cache.get('nonexistent')  # miss
        
        stats = self.cache.get_stats()
        
        self.assertEqual(stats['hits'], 2)
        self.assertEqual(stats['misses'], 1)
        self.assertEqual(stats['size'], 1)
    
    def test_cleanup_expired(self):
        """Test limpiar entradas expiradas"""
        cache = Cache(default_ttl=1)
        cache.set('key1', 'value1')
        
        time.sleep(1.5)
        
        cleaned = cache.cleanup_expired()
        
        self.assertEqual(cleaned, 1)
        self.assertEqual(len(cache._cache), 0)
    
    def test_serialization(self):
        """Test serialización y deserialización"""
        self.cache.set('key1', 'value1')
        self.cache.set('key2', 'value2')
        
        data = self.cache.to_dict()
        
        restored = Cache.from_dict(data)
        
        self.assertEqual(restored.get('key1'), 'value1')
        self.assertEqual(restored.get('key2'), 'value2')


class TestCachedDecorator(unittest.TestCase):
    """Tests para el decorador @cached"""
    
    def setUp(self):
        clear_cache()
    
    def test_cached_function(self):
        """Test función cacheada"""
        @cached(ttl=60, key_prefix='test')
        def expensive_function(x):
            return x * 2
        
        result1 = expensive_function(5)
        result2 = expensive_function(5)
        
        # Segunda llamada debe usar cache
        self.assertEqual(result1, result2)
    
    def test_different_args_different_cache(self):
        """Test que diferentes args tienen diferentes claves"""
        @cached(ttl=60)
        def compute(x):
            return x ** 2
        
        self.assertEqual(compute(2), 4)
        self.assertEqual(compute(3), 9)
    
    def test_clear_cache(self):
        """Test limpiar cache global"""
        @cached(ttl=60)
        def compute(x):
            return x * 2
        
        compute(5)
        
        clear_cache()
        
        # Verificar que se limpió (usando stats del cache interno)
        stats = compute._cache.get_stats()
        self.assertEqual(stats['hits'], 0)


class TestGlobalCache(unittest.TestCase):
    """Tests para cache global"""
    
    def test_get_cache_singleton(self):
        """Test que get_cache retorna singleton"""
        cache1 = get_cache()
        cache2 = get_cache()
        
        self.assertEqual(cache1, cache2)
    
    def test_clear_global_cache(self):
        """Test limpiar cache global"""
        cache = get_cache()
        cache.set('global_key', 'global_value')
        
        clear_cache()
        
        self.assertIsNone(cache.get('global_key'))


if __name__ == '__main__':
    unittest.main()