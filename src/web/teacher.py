from flask import render_template, session, redirect, url_for
from . import web_teacher_bp

@web_teacher_bp.route('/teacher/dashboard')
def teacher_dashboard():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('web_auth.login'))
    return render_template('teacher_dashboard.html', user_role='teacher', username=session.get('username', 'teacher'))

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
