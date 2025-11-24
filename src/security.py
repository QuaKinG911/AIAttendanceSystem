import os
import re
import logging
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
import hashlib
import shutil
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session

class InputValidator:
    """Validate and sanitize user inputs"""

    # Student ID pattern: alphanumeric, hyphens, underscores, max 20 chars
    STUDENT_ID_PATTERN = re.compile(r'^[A-Za-z0-9_-]{1,20}$')

    # Name pattern: letters, spaces, hyphens, apostrophes, max 50 chars
    NAME_PATTERN = re.compile(r"^[A-Za-z\s\-']{1,50}$")

    # Email pattern (basic validation)
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    @staticmethod
    def validate_student_id(student_id: str) -> Tuple[bool, str]:
        """Validate student ID"""
        if not student_id:
            return False, "Student ID cannot be empty"

        if not isinstance(student_id, str):
            return False, "Student ID must be a string"

        if not InputValidator.STUDENT_ID_PATTERN.match(student_id):
            return False, "Student ID contains invalid characters or is too long"

        return True, ""

    @staticmethod
    def validate_student_name(name: str) -> Tuple[bool, str]:
        """Validate student name"""
        if not name:
            return False, "Student name cannot be empty"

        if not isinstance(name, str):
            return False, "Student name must be a string"

        name = name.strip()
        if not name:
            return False, "Student name cannot be only whitespace"

        if not InputValidator.NAME_PATTERN.match(name):
            return False, "Student name contains invalid characters or is too long"

        return True, ""

    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Validate email address"""
        if not email:  # Email is optional
            return True, ""

        if not isinstance(email, str):
            return False, "Email must be a string"

        if not InputValidator.EMAIL_PATTERN.match(email):
            return False, "Invalid email format"

        return True, ""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal and other issues"""
        # Remove path separators and other dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = filename.replace('..', '')
        return filename.strip()

    @staticmethod
    def validate_image_data(image_data: bytes, max_size: int = 10*1024*1024) -> Tuple[bool, str]:
        """Validate image data"""
        if not image_data:
            return False, "Image data cannot be empty"

        if len(image_data) > max_size:
            return False, f"Image too large (max {max_size} bytes)"

        # Check for basic image signatures
        if len(image_data) < 4:
            return False, "Image data too small"

        # Check common image headers
        headers = {
            b'\xff\xd8\xff': 'JPEG',
            b'\x89PNG\r\n\x1a\n': 'PNG',
            b'GIF87a': 'GIF',
            b'GIF89a': 'GIF',
            b'BM': 'BMP'
        }

        for header, format_name in headers.items():
            if image_data.startswith(header):
                return True, ""

        return False, "Unsupported image format"


class SecureFileHandler:
    """Handle file operations securely"""

    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
    MAX_FILENAME_LENGTH = 255

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(exist_ok=True)

    def secure_path(self, filename: str, subdir: str = "") -> Tuple[bool, Path]:
        """Create a secure file path"""
        try:
            # Sanitize filename
            filename = InputValidator.sanitize_filename(filename)

            if not filename:
                return False, Path()

            if len(filename) > self.MAX_FILENAME_LENGTH:
                return False, Path()

            # Check extension
            ext = Path(filename).suffix.lower()
            if ext not in self.ALLOWED_EXTENSIONS:
                return False, Path()

            # Build secure path
            if subdir:
                full_path = (self.base_dir / subdir / filename).resolve()
                # Ensure path is within base directory
                if not str(full_path).startswith(str(self.base_dir)):
                    return False, Path()
            else:
                full_path = (self.base_dir / filename).resolve()
                if not str(full_path).startswith(str(self.base_dir)):
                    return False, Path()

            return True, full_path

        except Exception as e:
            logging.error(f"Error creating secure path: {e}")
            return False, Path()

    def save_file_securely(self, filename: str, data: bytes, subdir: str = "") -> Tuple[bool, str]:
        """Save file with security checks"""
        try:
            success, file_path = self.secure_path(filename, subdir)
            if not success:
                return False, "Invalid filename or path"

            # Create subdirectory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file atomically (write to temp file first)
            temp_path = file_path.with_suffix('.tmp')
            with open(temp_path, 'wb') as f:
                f.write(data)

            # Verify file was written correctly
            with open(temp_path, 'rb') as f:
                written_data = f.read()

            if len(written_data) != len(data):
                temp_path.unlink(missing_ok=True)
                return False, "File write verification failed"

            # Atomic move
            temp_path.replace(file_path)

            return True, str(file_path)

        except Exception as e:
            logging.error(f"Error saving file securely: {e}")
            return False, f"Failed to save file: {e}"

    def read_file_securely(self, filename: str, subdir: str = "") -> Tuple[bool, bytes]:
        """Read file with security checks"""
        try:
            success, file_path = self.secure_path(filename, subdir)
            if not success:
                return False, b""

            if not file_path.exists():
                return False, b""

            # Check file size (prevent reading very large files)
            max_size = 50 * 1024 * 1024  # 50MB
            if file_path.stat().st_size > max_size:
                return False, b""

            with open(file_path, 'rb') as f:
                data = f.read()

            return True, data

        except Exception as e:
            logging.error(f"Error reading file securely: {e}")
            return False, b""

    def delete_file_securely(self, filename: str, subdir: str = "") -> Tuple[bool, str]:
        """Delete file securely"""
        try:
            success, file_path = self.secure_path(filename, subdir)
            if not success:
                return False, "Invalid filename or path"

            if not file_path.exists():
                return False, "File does not exist"

            # Secure delete (overwrite before deleting)
            if file_path.stat().st_size > 0:
                with open(file_path, 'wb') as f:
                    f.write(b'\x00' * file_path.stat().st_size)

            file_path.unlink()
            return True, "File deleted successfully"

        except Exception as e:
            logging.error(f"Error deleting file securely: {e}")
            return False, f"Failed to delete file: {e}"

    def cleanup_directory(self, subdir: str = "", max_age_days: int = 30) -> int:
        """Clean up old files in directory"""
        try:
            import time

            if subdir:
                target_dir = (self.base_dir / subdir).resolve()
            else:
                target_dir = self.base_dir

            if not target_dir.exists():
                return 0

            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60
            deleted_count = 0

            for file_path in target_dir.rglob('*'):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        try:
                            file_path.unlink()
                            deleted_count += 1
                        except Exception as e:
                            logging.warning(f"Failed to delete old file {file_path}: {e}")

            return deleted_count

        except Exception as e:
            logging.error(f"Error during directory cleanup: {e}")
            return 0


class PrivacyManager:
    """Manage privacy and data protection"""

    def __init__(self):
        self.consent_required = True
        self.data_retention_days = 90
        self.anonymize_logs = True

    def check_consent(self, student_id: str) -> bool:
        """Check if student has given consent for processing"""
        # In a real implementation, this would check a consent database
        # For now, we'll assume consent is given during registration
        return True

    def anonymize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize sensitive data"""
        anonymized = data.copy()

        # Remove or hash sensitive information
        if 'email' in anonymized:
            anonymized['email'] = self._hash_string(anonymized['email'])

        if 'name' in anonymized:
            # Keep first letter of first name and full last name
            parts = anonymized['name'].split()
            if len(parts) >= 2:
                anonymized['name'] = f"{parts[0][0]}. {' '.join(parts[1:])}"
            else:
                anonymized['name'] = f"{parts[0][0]}."

        return anonymized

    def _hash_string(self, text: str) -> str:
        """Hash a string for anonymization"""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def should_retain_data(self, timestamp) -> bool:
        """Check if data should be retained based on retention policy"""
        import time
        from datetime import datetime

        if isinstance(timestamp, str):
            # Assume ISO format
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

        current_time = time.time()
        data_age_seconds = current_time - timestamp.timestamp()
        max_age_seconds = self.data_retention_days * 24 * 60 * 60

        return data_age_seconds <= max_age_seconds


# Password policy and security configuration
class SecurityConfig:
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL_CHARS = True
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_LOCKOUT_DURATION = 15  # minutes
    SESSION_TIMEOUT = 60  # minutes
    REQUIRE_HTTPS = True

class PasswordValidator:
    @staticmethod
    def validate_password(password):
        """Validate password against security policy"""
        errors = []
        
        if not password:
            errors.append("Password is required")
            return False, errors
        
        if len(password) < SecurityConfig.MIN_PASSWORD_LENGTH:
            errors.append(f"Password must be at least {SecurityConfig.MIN_PASSWORD_LENGTH} characters long")
        
        if len(password) > SecurityConfig.MAX_PASSWORD_LENGTH:
            errors.append(f"Password must not exceed {SecurityConfig.MAX_PASSWORD_LENGTH} characters")
        
        if SecurityConfig.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if SecurityConfig.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if SecurityConfig.REQUIRE_DIGITS and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if SecurityConfig.REQUIRE_SPECIAL_CHARS and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Check for common weak passwords
        weak_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey'
        ]
        if password.lower() in weak_passwords:
            errors.append("Password is too common. Please choose a stronger password")
        
        return len(errors) == 0, errors

class RateLimiter:
    def __init__(self):
        self.attempts = {}  # IP -> {count: int, last_attempt: datetime}
    
    def is_rate_limited(self, ip_address, max_attempts=None, lockout_duration=None):
        """Check if IP is rate limited"""
        if max_attempts is None:
            max_attempts = SecurityConfig.MAX_LOGIN_ATTEMPTS
        if lockout_duration is None:
            lockout_duration = SecurityConfig.LOGIN_LOCKOUT_DURATION
        
        now = datetime.now()
        
        if ip_address not in self.attempts:
            self.attempts[ip_address] = {'count': 0, 'last_attempt': now}
            return False
        
        attempts_data = self.attempts[ip_address]
        
        # Reset if lockout period has passed
        if now - attempts_data['last_attempt'] > timedelta(minutes=lockout_duration):
            attempts_data['count'] = 0
            attempts_data['last_attempt'] = now
            return False
        
        # Check if rate limited
        if attempts_data['count'] >= max_attempts:
            return True
        
        return False
    
    def record_attempt(self, ip_address):
        """Record a failed attempt"""
        now = datetime.now()
        if ip_address not in self.attempts:
            self.attempts[ip_address] = {'count': 1, 'last_attempt': now}
        else:
            self.attempts[ip_address]['count'] += 1
            self.attempts[ip_address]['last_attempt'] = now
    
    def clear_attempts(self, ip_address):
        """Clear attempts for successful login"""
        if ip_address in self.attempts:
            del self.attempts[ip_address]

def require_https(f):
    """Decorator to require HTTPS for production"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if SecurityConfig.REQUIRE_HTTPS and not request.is_secure:
            return jsonify({
                'error': 'HTTPS required',
                'message': 'This endpoint requires a secure HTTPS connection'
            }), 403
        return f(*args, **kwargs)
    return decorated_function

def generate_csrf_token():
    """Generate a new CSRF token"""
    return secrets.token_urlsafe(32)

def validate_csrf_token(f):
    """Decorator to validate CSRF tokens"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE']:
            token = request.headers.get('X-CSRF-Token')
            if not token or token != session.get('csrf_token'):
                return jsonify({
                    'error': 'Invalid CSRF token',
                    'message': 'CSRF validation failed'
                }), 403
        return f(*args, **kwargs)
    return decorated_function

# Global instances
input_validator = InputValidator()
file_handler = SecureFileHandler("data")
privacy_manager = PrivacyManager()
rate_limiter = RateLimiter()