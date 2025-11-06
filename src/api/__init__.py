# src/api/__init__.py - Flask API Application

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
from datetime import timedelta
from dotenv import load_dotenv

from src.models import db

def create_app():
    # Load environment variables from .env file
    load_dotenv()

    # Get the project root directory (parent of src)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    template_dir = os.path.join(project_root, 'templates')
    app = Flask(__name__, template_folder=template_dir)

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        'postgresql://attendance_user:attendance_pass@127.0.0.1/ai_attendance'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True

    # Initialize extensions
    CORS(app)
    JWTManager(app)
    limiter = Limiter(key_func=get_remote_address)
    limiter.init_app(app)
    db.init_app(app)

    # Register blueprints
    from .auth import auth_bp
    from .users import users_bp
    from .classes import classes_bp
    from .attendance import attendance_bp
    from .analytics import analytics_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(classes_bp, url_prefix='/api/classes')
    app.register_blueprint(attendance_bp, url_prefix='/api/attendance')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')

    # Health check endpoint
    @app.route('/api/health')
    def health():
        return {'status': 'healthy', 'message': 'AI Attendance API is running'}

    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)