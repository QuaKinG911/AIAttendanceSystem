# src/api/users.py - User management API endpoints

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.models import User

users_bp = Blueprint('users', __name__)

@users_bp.route('/', methods=['GET'])
@jwt_required()
def get_users():
    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'role': u.role.value
    } for u in users])

@users_bp.route('/', methods=['POST'])
@jwt_required()
def create_user():
    data = request.get_json()
    # Implementation for creating users
    return jsonify({'message': 'User created'}), 201