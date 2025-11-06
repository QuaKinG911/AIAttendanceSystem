# src/api/classes.py - Class management API endpoints

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

classes_bp = Blueprint('classes', __name__)

@classes_bp.route('/', methods=['GET'])
@jwt_required()
def get_classes():
    # Return list of classes
    return jsonify([])

@classes_bp.route('/', methods=['POST'])
@jwt_required()
def create_class():
    data = request.get_json()
    return jsonify({'message': 'Class created'}), 201