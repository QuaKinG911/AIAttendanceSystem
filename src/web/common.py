from flask import redirect, url_for
from . import web_common_bp

@web_common_bp.route('/')
def index():
    return redirect(url_for('web_auth.login'))
