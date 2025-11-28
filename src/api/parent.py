from flask import Blueprint, request, jsonify, session
from src.models import User, UserRole, AttendanceRecord, Enrollment, Class, Course, db
from datetime import datetime, timedelta
import logging

parent_bp = Blueprint('parent', __name__)
logger = logging.getLogger(__name__)

@parent_bp.route('/students', methods=['GET'])
def get_children():
    """Get students associated with the logged-in parent"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    # For now, since we don't have a Parent-Student relationship model yet,
    # we'll return all students for demonstration or a specific mock logic.
    # Ideally, there should be a parent_student table.
    # As a fallback/placeholder, we can return students with the same last name? 
    # Or just return all students if the user is a parent (demo mode).
    
    try:
        user = User.query.get(session['user_id'])
        if not user or user.role != UserRole.PARENT: # Assuming PARENT role exists or will be added
             return jsonify({'error': 'Unauthorized'}), 401

        # MOCK: Return all students for now to ensure the dashboard works
        students = User.query.filter_by(role=UserRole.STUDENT).all()
        
        return jsonify([{
            'id': s.id,
            'name': s.full_name or s.username,
            'grade': s.start_year,
            'school': 'AI High School' # Placeholder
        } for s in students])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@parent_bp.route('/students/<int:student_id>/attendance', methods=['GET'])
def get_student_attendance(student_id):
    """Get attendance for a specific child"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    try:
        # Verify student exists
        student = User.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404
            
        # Get attendance records
        records = AttendanceRecord.query.filter_by(student_id=student_id).order_by(AttendanceRecord.detected_at.desc()).limit(50).all()
        
        return jsonify([{
            'date': r.detected_at.strftime('%Y-%m-%d'),
            'time': r.detected_at.strftime('%H:%M'),
            'status': r.status,
            'course': r.session.name if r.session else 'Unknown'
        } for r in records])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@parent_bp.route('/appeals', methods=['POST'])
def submit_appeal():
    """Submit an attendance appeal"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    try:
        data = request.get_json()
        # Logic to save appeal would go here
        # For now just return success
        return jsonify({'message': 'Appeal submitted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
