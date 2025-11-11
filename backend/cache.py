"""
Redis Cache Service
Handles caching of verdicts, API responses, and session data
"""
import redis
import json
import os
from typing import Optional, Any
from functools import wraps
import hashlib

class RedisCache:
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            self.client = redis.from_url(redis_url, decode_responses=True)
            self.enabled = True
        except Exception as e:
            print(f"Redis connection failed: {e}. Caching disabled.")
            self.client = None
            self.enabled = False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            print(f"Cache get error: {e}")
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL (default 1 hour)"""
        if not self.enabled:
            return False
        try:
            self.client.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str):
        """Delete key from cache"""
        if not self.enabled:
            return False
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern"""
        if not self.enabled:
            return False
        try:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
            return True
        except Exception as e:
            print(f"Cache clear error: {e}")
            return False
    
    def check_connection(self) -> bool:
        """Check if Redis connection is working"""
        if not self.enabled:
            return False
        try:
            return self.client.ping()
        except Exception as e:
            print(f"Redis ping failed: {e}")
            return False


# Decorator for caching function results
def cache_result(ttl: int = 3600, key_prefix: str = ""):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            arg_str = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
            cache_key = f"{key_prefix}:{func.__name__}:{hashlib.md5(arg_str.encode()).hexdigest()}"
            
            # Try to get from cache
            cached = cache.get(cache_key)
            if cached is not None:
                print(f"Cache hit: {cache_key}")
                return cached
            
            # Execute function
            print(f"Cache miss: {cache_key}")
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


# Global cache instance
cache = RedisCache()


# Specific cache functions for AI Judge
def cache_verdict(case_id: str, verdict: dict, ttl: int = 86400):
    """Cache a verdict (24 hours by default)"""
    return cache.set(f"verdict:{case_id}", verdict, ttl)


def get_cached_verdict(case_id: str) -> Optional[dict]:
    """Get cached verdict"""
    return cache.get(f"verdict:{case_id}")


def cache_case_data(case_id: str, data: dict, ttl: int = 3600):
    """Cache case data (1 hour by default)"""
    return cache.set(f"case:{case_id}", data, ttl)


def get_cached_case(case_id: str) -> Optional[dict]:
    """Get cached case data"""
    return cache.get(f"case:{case_id}")


def invalidate_case_cache(case_id: str):
    """Invalidate all cache for a case"""
    cache.delete(f"verdict:{case_id}")
    cache.delete(f"case:{case_id}")
    cache.clear_pattern(f"followup:{case_id}:*")
