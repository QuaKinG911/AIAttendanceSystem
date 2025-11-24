# src/cache.py - Redis caching configuration

import redis
from flask_caching import Cache
import os

# Redis configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Initialize Redis client
redis_client = redis.from_url(REDIS_URL)

# Flask-Caching configuration
cache_config = {
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': REDIS_URL,
    'CACHE_DEFAULT_TIMEOUT': 300,  # 5 minutes default
    'CACHE_KEY_PREFIX': 'attendance_system:',
}

# Initialize Flask-Caching
cache = Cache(config=cache_config)

# Cache keys
class CacheKeys:
    # User-related caches
    USER_PROFILE = 'user:profile:{}'
    USER_PERMISSIONS = 'user:permissions:{}'

    # Attendance caches
    ATTENDANCE_STATS = 'attendance:stats:{}:{}'  # student_id, period
    ATTENDANCE_RECORDS = 'attendance:records:{}:{}:{}'  # student_id, start_date, end_date
    ATTENDANCE_CHART = 'attendance:chart:{}:{}'  # student_id, days

    # Class and course caches
    CLASS_LIST = 'class:list'
    CLASS_DETAILS = 'class:details:{}'
    COURSE_SCHEDULE = 'course:schedule:{}'  # class_id

    # Analytics caches
    ANALYTICS_OVERVIEW = 'analytics:overview'
    ANALYTICS_TRENDS = 'analytics:trends:{}'  # period

    # System caches
    SYSTEM_CONFIG = 'system:config'
    ANNOUNCEMENTS_ACTIVE = 'announcements:active'

# Cache TTL configurations (in seconds)
CACHE_TTL = {
    'user_profile': 3600,      # 1 hour
    'user_permissions': 1800,  # 30 minutes
    'attendance_stats': 900,   # 15 minutes
    'attendance_records': 1800, # 30 minutes
    'attendance_chart': 3600,  # 1 hour
    'class_list': 1800,        # 30 minutes
    'class_details': 3600,     # 1 hour
    'course_schedule': 1800,   # 30 minutes
    'analytics_overview': 600, # 10 minutes
    'analytics_trends': 1800,  # 30 minutes
    'system_config': 7200,     # 2 hours
    'announcements': 600,      # 10 minutes
}

def get_cache_key(key_template, *args):
    """Generate cache key from template and arguments"""
    return key_template.format(*args)

def invalidate_user_cache(user_id):
    """Invalidate all caches related to a specific user"""
    keys_to_delete = [
        get_cache_key(CacheKeys.USER_PROFILE, user_id),
        get_cache_key(CacheKeys.USER_PERMISSIONS, user_id),
    ]

    # Also invalidate attendance caches for this user
    # This is a simplified approach - in production, you might want to use Redis SCAN
    try:
        pattern = f"attendance:*:stats:{user_id}:*"
        matching_keys = redis_client.keys(pattern)
        if matching_keys:
            keys_to_delete.extend(matching_keys)

        pattern = f"attendance:*:records:{user_id}:*"
        matching_keys = redis_client.keys(pattern)
        if matching_keys:
            keys_to_delete.extend(matching_keys)
    except Exception as e:
        # Log error but don't fail the operation
        print(f"Error finding cache keys to invalidate: {e}")

    if keys_to_delete:
        redis_client.delete(*keys_to_delete)

def invalidate_class_cache(class_id):
    """Invalidate all caches related to a specific class"""
    keys_to_delete = [
        get_cache_key(CacheKeys.CLASS_DETAILS, class_id),
        get_cache_key(CacheKeys.COURSE_SCHEDULE, class_id),
    ]

    # Invalidate attendance caches for all students in this class
    # This would require querying the database, so we'll use a simpler approach
    redis_client.delete(*keys_to_delete)

def invalidate_system_cache():
    """Invalidate system-wide caches"""
    keys_to_delete = [
        CacheKeys.CLASS_LIST,
        CacheKeys.SYSTEM_CONFIG,
        CacheKeys.ANNOUNCEMENTS_ACTIVE,
        CacheKeys.ANALYTICS_OVERVIEW,
    ]
    redis_client.delete(*keys_to_delete)

# Cache decorators for common patterns
def cache_user_data(timeout=None):
    """Decorator to cache user-specific data"""
    def decorator(f):
        @cache.memoize(timeout=timeout or CACHE_TTL['user_profile'])
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapper
    return decorator

def cache_attendance_data(timeout=None):
    """Decorator to cache attendance-related data"""
    def decorator(f):
        @cache.memoize(timeout=timeout or CACHE_TTL['attendance_stats'])
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapper
    return decorator

def cache_analytics_data(timeout=None):
    """Decorator to cache analytics data"""
    def decorator(f):
        @cache.memoize(timeout=timeout or CACHE_TTL['analytics_overview'])
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapper
    return decorator