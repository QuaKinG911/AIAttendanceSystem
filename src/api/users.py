# src/api/users.py - User management API endpoints

from flask import Blueprint, request, jsonify, session, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models import User
from functools import wraps

users_bp = Blueprint('users', __name__)

def session_or_jwt_required(f):
    """Decorator that allows either JWT auth or session auth"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Try JWT first
        try:
            jwt_user = get_jwt_identity()
            if jwt_user:
                user = User.query.filter_by(username=jwt_user).first()
                if user:
                    g.user = user
                    return f(*args, **kwargs)
        except:
            pass

        # Fall back to session auth
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user:
                g.user = user
                return f(*args, **kwargs)

        return jsonify({'error': 'Authentication required'}), 401

    return decorated_function

@users_bp.route('/', methods=['GET'])
@session_or_jwt_required
def get_users():
    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'role': u.role.value
    } for u in users])

@users_bp.route('/', methods=['POST'])
@session_or_jwt_required
def create_user():
    data = request.get_json()
    # Implementation for creating users
    return jsonify({'message': 'User created'}), 201