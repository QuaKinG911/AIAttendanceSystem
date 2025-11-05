#!/usr/bin/env python3
"""
Simple test Streamlit app
"""

import streamlit as st
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.dataset_manager import list_students
from main import SimpleAttendanceSystem

st.set_page_config(page_title='AI Attendance Test', page_icon='🎓')

st.title('🎓 AI Attendance System - Test')

# Test components
st.header('System Status')

try:
    # Test dataset
    students = list_students()
    st.success(f'✅ Dataset loaded: {len(students)} students')
    st.table([{'ID': sid, 'Name': name} for sid, name in students])

    # Test system initialization
    system = SimpleAttendanceSystem()
    st.success('✅ Attendance system initialized')

    # Show attendance records
    if system.attendance_records:
        st.header('Current Attendance')
        for student_id, record in system.attendance_records.items():
            st.write(f"**{record['name']}** ({student_id}) - {record['time']}")
    else:
        st.info('No attendance records yet. Start a session to begin tracking.')

except Exception as e:
    st.error(f'❌ Error: {e}')
    st.code(str(e))

st.header('Controls')
if st.button('Test Face Detection'):
    st.info('Face detection test would run here')

st.caption('This is a test version of the Streamlit app')