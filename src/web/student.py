from flask import render_template, session, redirect, url_for
from . import web_student_bp

@web_student_bp.route('/student/dashboard')
def student_dashboard():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('web_auth.login'))
    return render_template('student_dashboard.html', user_role='student', username=session.get('username', 'student'))

@web_student_bp.route('/student/attendance')
def student_attendance():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('web_auth.login'))
    return render_template('student_attendance.html', user_role='student', username=session.get('username', 'student'))
