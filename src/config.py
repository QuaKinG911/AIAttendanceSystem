import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigManager:
    """Centralized configuration management for AI Attendance System"""

    def __init__(self, config_file: str = "config/settings.json"):
        self.config_file = Path(__file__).parent.parent / config_file
        self.config_dir = self.config_file.parent
        self.config_dir.mkdir(exist_ok=True)
        self._config = {}
        self._load_config()

    def _load_config(self):
        """Load configuration from file and environment variables"""
        # Default configuration
        self._config = {
            "camera": {
                "source": int(os.getenv("ATTENDANCE_CAMERA_SOURCE", "0")),
                "resolution": {
                    "width": int(os.getenv("ATTENDANCE_CAMERA_WIDTH", "1280")),
                    "height": int(os.getenv("ATTENDANCE_CAMERA_HEIGHT", "720"))
                },
                "fps": int(os.getenv("ATTENDANCE_CAMERA_FPS", "30"))
            },
            "attendance": {
                "duration_minutes": int(os.getenv("ATTENDANCE_DURATION_MINUTES", "5")),
                "confidence_threshold": float(os.getenv("ATTENDANCE_CONFIDENCE_THRESHOLD", "0.7")),
                "liveness_threshold": float(os.getenv("ATTENDANCE_LIVENESS_THRESHOLD", "0.6"))
            },
            "detection": {
                "model": os.getenv("ATTENDANCE_DETECTION_MODEL", "yolo"),
                "confidence_threshold": float(os.getenv("ATTENDANCE_DETECTION_CONFIDENCE", "0.5")),
                "fallback_to_haar": os.getenv("ATTENDANCE_FALLBACK_HAAR", "true").lower() == "true"
            },
            "recognition": {
                "model": os.getenv("ATTENDANCE_RECOGNITION_MODEL", "facenet"),
                "tolerance": float(os.getenv("ATTENDANCE_RECOGNITION_TOLERANCE", "0.6")),
                "database_path": os.getenv("ATTENDANCE_DATABASE_PATH", "data/face_encodings/face_database.pkl")
            },
            "liveness": {
                "enabled": os.getenv("ATTENDANCE_LIVENESS_ENABLED", "true").lower() == "true",
                "method": os.getenv("ATTENDANCE_LIVENESS_METHOD", "mediapipe"),
                "threshold": float(os.getenv("ATTENDANCE_LIVENESS_THRESHOLD", "0.6"))
            },
            "database": {
                "url": os.getenv("ATTENDANCE_DATABASE_URL", "sqlite:///data/attendance.db")
            },
            "logging": {
                "level": os.getenv("ATTENDANCE_LOG_LEVEL", "INFO"),
                "file": os.getenv("ATTENDANCE_LOG_FILE", "logs/attendance_system.log")
            },
            "performance": {
                "max_fps": int(os.getenv("ATTENDANCE_MAX_FPS", "30")),
                "batch_size": int(os.getenv("ATTENDANCE_BATCH_SIZE", "1")),
                "use_gpu": os.getenv("ATTENDANCE_USE_GPU", "auto")
            }
        }

        # Load from file if exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                self._merge_config(file_config)
                logging.info(f"Loaded configuration from {self.config_file}")
            except Exception as e:
                logging.warning(f"Failed to load config file {self.config_file}: {e}")

    def _merge_config(self, file_config: Dict[str, Any]):
        """Merge file configuration with defaults"""
        def merge_dict(target: Dict, source: Dict):
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    merge_dict(target[key], value)
                else:
                    target[key] = value

        merge_dict(self._config, file_config)

    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
            logging.info(f"Saved configuration to {self.config_file}")
        except Exception as e:
            logging.error(f"Failed to save config file {self.config_file}: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated key"""
        keys = key.split('.')
        value = self._config
        try:
            for k in keys:
                value = value[k]
            return value
        except KeyError:
            return default

    def set(self, key: str, value: Any):
        """Set configuration value by dot-separated key"""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def __setitem__(self, key: str, value: Any):
        self.set(key, value)

    def to_dict(self) -> Dict[str, Any]:
        """Return copy of configuration as dictionary"""
        import copy
        return copy.deepcopy(self._config)

# Global configuration instance
config = ConfigManager()