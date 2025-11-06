# src/api/attendance.py - Attendance API endpoints

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/', methods=['GET'])
@jwt_required()
def get_attendance():
    return jsonify([])

@attendance_bp.route('/start', methods=['POST'])
@jwt_required()
def start_session():
    return jsonify({'message': 'Session started'}), 201