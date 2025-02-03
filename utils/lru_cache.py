from collections import OrderedDict
from functools import wraps
import copy
def lru_cache(maxsize=128):
    """
    A custom LRU cache decorator that uses a hash of (args, kwargs) to generate cache keys.

    :param maxsize: Maximum number of cache entries to store. (Default: 128)
    """
    def decorator(func):
        cache = OrderedDict()

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a cache key by hashing a tuple of:
            # - args
            # - a frozenset of the kwargs items (so it can be hashed)
            cache_key = hash((args, frozenset(kwargs.items())))

            if cache_key in cache:
                # If the result is in the cache, move it to the end to mark it as recently used
                cache.move_to_end(cache_key)
                return cache[cache_key]
            
            # Otherwise, compute the result
            # print("args", args, "kwargs", frozenset(kwargs.items()), ", key = ", cache_key)
            result = func(*args, **kwargs)
            # Store it in the cache
            cache[cache_key] =copy.copy(result)
            cache.move_to_end(cache_key)

            # If we exceed maxsize, remove the least recently used item
            if len(cache) > maxsize:
                cache.popitem(last=False)

            return result

        return wrapper
    return decorator