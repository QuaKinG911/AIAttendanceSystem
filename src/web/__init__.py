from flask import Blueprint

web_auth_bp = Blueprint('web_auth', __name__)
web_student_bp = Blueprint('web_student', __name__)
web_teacher_bp = Blueprint('web_teacher', __name__)
web_admin_bp = Blueprint('web_admin', __name__)
web_parent_bp = Blueprint('web_parent', __name__)
web_common_bp = Blueprint('web_common', __name__)

from . import auth, student, teacher, admin, parent, common
