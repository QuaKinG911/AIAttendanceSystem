# run_web.py - Script to run the web application

#!/usr/bin/env python3

import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from app import app
from src.scheduling import init_scheduler

if __name__ == '__main__':
    print("Starting AI Attendance System Web Application...")
    print("Access at: http://localhost:5000")
    print("Login credentials:")
    print("  Admin: admin / admin456")
    print("  Teacher: teacher1 / teacher123")
    print("  Student: student1 / student123")
    print()

    # Initialize scheduler with app context
    # with app.app_context():
    #     init_scheduler()

    app.run(debug=True, host='0.0.0.0', port=5000)