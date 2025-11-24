from flask import render_template, session, redirect, url_for
from . import web_parent_bp

@web_parent_bp.route('/parent/dashboard')
def parent_dashboard():
    if 'user_id' not in session or session.get('role') != 'parent':
        return redirect(url_for('web_auth.login'))
    return render_template('parent_dashboard.html', user_role='parent', username=session.get('username', 'parent'))
