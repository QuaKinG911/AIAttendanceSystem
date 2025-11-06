# src/api/analytics.py - Analytics API endpoints

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/trends', methods=['GET'])
@jwt_required()
def get_trends():
    return jsonify({'trends': []})

@analytics_bp.route('/performance', methods=['GET'])
@jwt_required()
def get_performance():
    return jsonify({'performance': []})