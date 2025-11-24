from flask import render_template, session, redirect, url_for
from . import web_admin_bp

@web_admin_bp.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('web_auth.login'))
    return render_template('admin_dashboard.html', user_role='admin', username=session.get('username', 'admin'))

@web_admin_bp.route('/admin/users')
def admin_users():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('web_auth.login'))
    return render_template('admin_users.html', user_role='admin', username=session.get('username', 'admin'))

@web_admin_bp.route('/admin/announcements')
def admin_announcements():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('web_auth.login'))
    return render_template('admin_announcements.html', user_role='admin', username=session.get('username', 'admin'))

@web_admin_bp.route('/admin/ml-insights')
def admin_ml_insights():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('web_auth.login'))
    return render_template('admin_ml_insights.html', user_role='admin', username=session.get('username', 'admin'))

@web_admin_bp.route('/admin/classes')
def admin_classes():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('web_auth.login'))
    return render_template('admin_classes.html', user_role='admin', username=session.get('username', 'admin'))

@web_admin_bp.route('/admin/admins')
def admin_admins():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('web_auth.login'))
    return render_template('admin_admins.html', user_role='admin', username=session.get('username', 'admin'))

@web_admin_bp.route('/admin/students')
def admin_students():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('web_auth.login'))
    return render_template('admin_students.html', user_role='admin', username=session.get('username', 'admin'))

@web_admin_bp.route('/admin/teachers')
def admin_teachers():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('web_auth.login'))
    return render_template('admin_teachers.html', user_role='admin', username=session.get('username', 'admin'))

@web_admin_bp.route('/admin/analytics')
def admin_analytics():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('web_auth.login'))
    return render_template('admin_analytics.html', user_role='admin', username=session.get('username', 'admin'))
