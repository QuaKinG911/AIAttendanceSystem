from flask import render_template, session, redirect, url_for
from . import web_student_bp

from src.models import Enrollment, Class, Course, User

@web_student_bp.route('/student/dashboard')
def student_dashboard():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('web_auth.login'))
    
    user_id = session['user_id']
    enrollment = Enrollment.query.filter_by(student_id=user_id).first()
    
    schedule = []
    class_name = None
    
    if enrollment:
        class_obj = Class.query.get(enrollment.class_id)
        if class_obj:
            class_name = class_obj.name
            courses = Course.query.filter_by(class_id=enrollment.class_id).all()
            
            # Serialize courses for the template
            for course in courses:
                teacher = User.query.get(course.teacher_id)
                teacher_name = teacher.full_name if teacher else "Unknown"
                
                schedule.append({
                    'id': course.id,
                    'name': course.name,
                    'day_of_week': course.day_of_week,
                    'start_time': course.start_time.strftime('%H:%M'),
                    'end_time': course.end_time.strftime('%H:%M'),
                    'room': course.room,
                    'teacher_name': teacher_name
                })

    return render_template('student_dashboard.html', 
                         user_role='student', 
                         username=session.get('username', 'student'),
                         schedule=schedule,
                         class_name=class_name)

@web_student_bp.route('/student/attendance')
def student_attendance():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('web_auth.login'))
    return render_template('student_attendance.html', user_role='student', username=session.get('username', 'student'))
