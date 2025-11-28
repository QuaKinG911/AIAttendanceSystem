from flask import render_template, session, redirect, url_for
from . import web_teacher_bp

from src.models import Course, Class

@web_teacher_bp.route('/teacher/dashboard')
def teacher_dashboard():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('web_auth.login'))
    
    user_id = session['user_id']
    courses = Course.query.filter_by(teacher_id=user_id).all()
    
    schedule = []
    
    for course in courses:
        # Get class name for context
        class_obj = Class.query.get(course.class_id)
        class_name = class_obj.name if class_obj else "Unknown Class"
        
        schedule.append({
            'id': course.id,
            'name': course.name,
            'day_of_week': course.day_of_week,
            'start_time': course.start_time.strftime('%H:%M'),
            'end_time': course.end_time.strftime('%H:%M'),
            'room': course.room,
            'class_name': class_name
        })

    return render_template('teacher_dashboard.html', 
                         user_role='teacher', 
                         username=session.get('username', 'teacher'),
                         schedule=schedule)

@web_teacher_bp.route('/teacher/classes')
def teacher_classes():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('web_auth.login'))
    return render_template('teacher_classes.html', user_role='teacher', username=session.get('username', 'teacher'))

@web_teacher_bp.route('/teacher/attendance')
def teacher_attendance():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('web_auth.login'))
    return render_template('teacher_attendance.html', user_role='teacher', username=session.get('username', 'teacher'))

@web_teacher_bp.route('/teacher/live-attendance')
def live_attendance():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('web_auth.login'))
    return render_template('live_attendance.html', user_role='teacher', username=session.get('username', 'teacher'))

@web_teacher_bp.route('/teacher/classes/<int:class_id>')
def teacher_class_details(class_id):
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('web_auth.login'))
    
    class_obj = Class.query.get(class_id)
    if not class_obj:
        return redirect(url_for('web_teacher.teacher_classes'))
        
    return render_template('teacher_class_details.html', 
                         user_role='teacher', 
                         username=session.get('username', 'teacher'),
                         class_id=class_id,
                         class_name=class_obj.name)
