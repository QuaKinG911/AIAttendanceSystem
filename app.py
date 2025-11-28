from src.api import create_app
from src.models import db, User, UserRole, Class, Course
from src.web import web_auth_bp, web_student_bp, web_teacher_bp, web_admin_bp, web_parent_bp, web_common_bp
import logging
from datetime import datetime

# Create Flask app
app = create_app()

# Register Web Blueprints
app.register_blueprint(web_auth_bp)
app.register_blueprint(web_student_bp)
app.register_blueprint(web_teacher_bp)
app.register_blueprint(web_admin_bp)
app.register_blueprint(web_parent_bp)
app.register_blueprint(web_common_bp)

from flask import send_from_directory
import os

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(os.path.join(os.getcwd(), 'uploads'), filename)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("app.log"),
                        logging.StreamHandler()
                    ])

# Initialize database
with app.app_context():
    db.create_all()
    # Create default users if not exist
    try:
        if User.query.count() == 0:
            logging.info("Creating default users...")
            admin = User()
            admin.username = 'admin'
            admin.email = 'admin@school.edu'
            admin.role = UserRole.ADMIN
            admin.set_password('admin456')

            teacher = User()
            teacher.username = 'teacher'
            teacher.email = 'teacher@school.edu'
            teacher.role = UserRole.TEACHER
            teacher.set_password('teacher123')

            student = User()
            student.username = 'student'
            student.email = 'student@school.edu'
            student.role = UserRole.STUDENT
            student.set_password('student123')

            db.session.add_all([admin, teacher, student])
            db.session.commit()

            # Create sample classes and courses
            try:
                # Create a sample class
                sample_class = Class()
                sample_class.name = "2025 Bachelor's of Computer Science"
                db.session.add(sample_class)
                db.session.commit()

                # Create sample courses for the teacher
                courses_data = [
                    ("Introduction to Programming", 1, "08:00", "09:30", "Room 101"),
                    ("Data Structures", 2, "10:00", "11:30", "Room 102"),
                    ("Database Systems", 3, "14:00", "15:30", "Room 103"),
                    ("Web Development", 4, "16:00", "17:30", "Room 104"),
                    ("Machine Learning", 5, "09:00", "10:30", "Lab 201")
                ]

                for course_name, day, start, end, room in courses_data:
                    course = Course()
                    course.class_id = sample_class.id
                    course.name = course_name
                    course.teacher_id = teacher.id
                    course.start_time = datetime.strptime(start, "%H:%M").time()
                    course.end_time = datetime.strptime(end, "%H:%M").time()
                    course.room = room
                    course.day_of_week = day
                    db.session.add(course)

                db.session.commit()
                logging.info("Sample classes and courses created.")

            except Exception as e:
                logging.error(f"Error creating sample data: {e}")
                db.session.rollback()

            logging.info("Default users created.")
    except Exception as e:
        logging.error(f"Error creating default users: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)