import time
import threading
import logging
from typing import Dict, List, Optional, Callable
from collections import deque
import psutil
import os
import numpy as np

class PerformanceMonitor:
    """Monitor system performance metrics"""

    def __init__(self, max_samples: int = 100):
        self.max_samples = max_samples
        self.frame_times = deque(maxlen=max_samples)
        self.detection_times = deque(maxlen=max_samples)
        self.recognition_times = deque(maxlen=max_samples)
        self.memory_usage = deque(maxlen=max_samples)
        self.cpu_usage = deque(maxlen=max_samples)

        self.start_time = time.time()
        self.frame_count = 0

    def record_frame_time(self, duration: float):
        """Record frame processing time"""
        self.frame_times.append(duration)
        self.frame_count += 1

    def record_detection_time(self, duration: float):
        """Record face detection time"""
        self.detection_times.append(duration)

    def record_recognition_time(self, duration: float):
        """Record face recognition time"""
        self.recognition_times.append(duration)

    def record_system_metrics(self):
        """Record system resource usage"""
        try:
            process = psutil.Process(os.getpid())
            self.memory_usage.append(process.memory_info().rss / 1024 / 1024)  # MB
            self.cpu_usage.append(process.cpu_percent())
        except Exception as e:
            logging.debug(f"Failed to record system metrics: {e}")

    def get_fps(self) -> float:
        """Calculate current FPS"""
        if not self.frame_times:
            return 0.0
        return 1.0 / (sum(self.frame_times) / len(self.frame_times))

    def get_average_times(self) -> Dict[str, float]:
        """Get average processing times"""
        return {
            'frame_time': sum(self.frame_times) / len(self.frame_times) if self.frame_times else 0,
            'detection_time': sum(self.detection_times) / len(self.detection_times) if self.detection_times else 0,
            'recognition_time': sum(self.recognition_times) / len(self.recognition_times) if self.recognition_times else 0,
        }

    def get_system_metrics(self) -> Dict[str, float]:
        """Get system resource metrics"""
        return {
            'memory_mb': sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0,
            'cpu_percent': sum(self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0,
        }

    def get_stats(self) -> Dict:
        """Get comprehensive performance statistics"""
        return {
            'fps': self.get_fps(),
            'total_frames': self.frame_count,
            'uptime_seconds': time.time() - self.start_time,
            'averages': self.get_average_times(),
            'system': self.get_system_metrics(),
        }


class OptimizedFaceMatcher:
    """Optimized face matcher with caching and batch processing"""

    def __init__(self, base_matcher, cache_size: int = 50):
        self.base_matcher = base_matcher
        self.cache_size = cache_size
        self.encoding_cache = {}  # face_image_hash -> encoding
        self.recognition_cache = {}  # encoding_hash -> (id, name, confidence)

        # LRU cache for recognition results
        self.cache_order = deque(maxlen=cache_size)

    def _hash_encoding(self, encoding: np.ndarray) -> str:
        """Create hash for encoding cache"""
        import hashlib
        return hashlib.md5(encoding.tobytes()).hexdigest()

    def extract_face_features(self, face_image):
        """Extract features with caching"""
        # Simple image hash for caching
        img_hash = hash(face_image.tobytes())

        if img_hash in self.encoding_cache:
            return self.encoding_cache[img_hash]

        encoding = self.base_matcher.extract_face_features(face_image)

        if encoding is not None and len(self.encoding_cache) < self.cache_size:
            self.encoding_cache[img_hash] = encoding

        return encoding

    def recognize_face(self, face_encoding):
        """Recognize face with caching"""
        encoding_hash = self._hash_encoding(face_encoding)

        if encoding_hash in self.recognition_cache:
            # Move to front of LRU cache
            self.cache_order.remove(encoding_hash)
            self.cache_order.append(encoding_hash)
            return self.recognition_cache[encoding_hash]

        result = self.base_matcher.recognize_face(face_encoding)

        # Cache result
        if len(self.recognition_cache) < self.cache_size:
            self.recognition_cache[encoding_hash] = result
            self.cache_order.append(encoding_hash)
        elif self.cache_order:
            # Remove oldest cache entry
            oldest = self.cache_order.popleft()
            del self.recognition_cache[oldest]
            self.recognition_cache[encoding_hash] = result
            self.cache_order.append(encoding_hash)

        return result

    def clear_cache(self):
        """Clear all caches"""
        self.encoding_cache.clear()
        self.recognition_cache.clear()
        self.cache_order.clear()


class AsyncProcessor:
    """Asynchronous processing for better performance"""

    def __init__(self, max_workers: int = 2):
        self.max_workers = max_workers
        self.executor = None
        self._init_executor()

    def _init_executor(self):
        """Initialize thread pool executor"""
        try:
            from concurrent.futures import ThreadPoolExecutor
            self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        except ImportError:
            logging.warning("ThreadPoolExecutor not available, falling back to synchronous processing")
            self.executor = None

    def submit_task(self, func: Callable, *args, **kwargs):
        """Submit task for asynchronous execution"""
        if self.executor:
            return self.executor.submit(func, *args, **kwargs)
        else:
            # Synchronous fallback
            return SynchronousFuture(func(*args, **kwargs))

    def shutdown(self):
        """Shutdown the executor"""
        if self.executor:
            self.executor.shutdown(wait=True)


class SynchronousFuture:
    """Synchronous future for fallback when threading is not available"""

    def __init__(self, result):
        self.result = result
        self._done = True

    def done(self):
        return self._done

    def result(self, timeout=None):
        return self.result


class ResourceManager:
    """Manage system resources efficiently"""

    def __init__(self):
        self.resources = {}
        self.lock = threading.Lock()

    def get_resource(self, name: str, factory: Callable):
        """Get or create a resource"""
        with self.lock:
            if name not in self.resources:
                self.resources[name] = factory()
            return self.resources[name]

    def cleanup_resource(self, name: str):
        """Clean up a specific resource"""
        with self.lock:
            if name in self.resources:
                resource = self.resources[name]
                if hasattr(resource, 'cleanup'):
                    resource.cleanup()
                elif hasattr(resource, 'close'):
                    resource.close()
                elif hasattr(resource, 'shutdown'):
                    resource.shutdown()
                del self.resources[name]

    def cleanup_all(self):
        """Clean up all resources"""
        with self.lock:
            for name in list(self.resources.keys()):
                self.cleanup_resource(name)


# Global instances
performance_monitor = PerformanceMonitor()
resource_manager = ResourceManager()
async_processor = AsyncProcessor()