import os
import time
import io
import logging
from datetime import datetime, timedelta

import streamlit as st
import numpy as np
import cv2

# Suppress inotify and other verbose logging in Streamlit
logging.getLogger('watchdog').setLevel(logging.WARNING)
logging.getLogger('streamlit').setLevel(logging.WARNING)

# Make local modules importable
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from main import SimpleAttendanceSystem  # uses OpenCV and our detectors with fallbacks
from src.utils.dataset_manager import (
    add_student,
    remove_student,
    list_students,
    ensure_dataset_dirs,
)


TITLE = 'AI Attendance - Streamlit'


def init_session_state() -> None:
    if 'running' not in st.session_state:
        st.session_state.running = False
    if 'duration_minutes' not in st.session_state:
        st.session_state.duration_minutes = 5
    if 'session_start' not in st.session_state:
        st.session_state.session_start = None
    if 'attendance_count' not in st.session_state:
        st.session_state.attendance_count = 0
    if 'system' not in st.session_state:
        st.session_state.system = None
    # Sanity checks
    faces_dir = os.path.join(PROJECT_ROOT, 'data', 'faces')
    models_dir = os.path.join(PROJECT_ROOT, 'models')
    os.makedirs(faces_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)


def format_remaining() -> str:
    if not st.session_state.session_start:
        return 'Not started'
    elapsed = datetime.now() - st.session_state.session_start
    remaining = timedelta(minutes=st.session_state.duration_minutes) - elapsed
    secs = int(max(0, remaining.total_seconds()))
    return f'{secs//60}:{secs%60:02d}'


def draw_header():
    st.title(TITLE)
    st.caption('Start attendance, set a timer, and manage student dataset (add/remove).')


def side_controls(system: SimpleAttendanceSystem):
    st.sidebar.header('🎛️ Controls')

    # Configuration section
    with st.sidebar.expander('⚙️ Settings', expanded=False):
        st.session_state.duration_minutes = st.number_input(
            'Attendance duration (minutes)', min_value=1, max_value=120,
            value=st.session_state.duration_minutes, step=1, key='duration_input'
        )

        confidence_threshold = st.slider(
            'Recognition Confidence Threshold',
            min_value=0.1, max_value=1.0, value=0.7, step=0.1,
            help="Minimum confidence for marking attendance"
        )

        liveness_enabled = st.checkbox('Enable Liveness Detection', value=True,
                                     help="Check for live faces vs photos/videos")

    # Control buttons
    st.sidebar.subheader('Session Control')
    col1, col2 = st.sidebar.columns(2)
    if col1.button('🚀 Start Class', disabled=st.session_state.running, use_container_width=True):
        st.session_state.running = True
        st.session_state.session_start = datetime.now()
        system.session_start = st.session_state.session_start
        system.attendance_duration = st.session_state.duration_minutes
        st.success('Class session started!')

    if col2.button('⏹️ Stop Class', disabled=not st.session_state.running, use_container_width=True):
        st.session_state.running = False
        st.session_state.session_start = None
        st.info('Class session stopped.')

    # Status metrics
    st.sidebar.subheader('📊 Status')
    st.sidebar.metric('⏰ Time Remaining', format_remaining())
    st.sidebar.metric('👥 Marked Attendance', len(system.attendance_records))

    # System info
    with st.sidebar.expander('ℹ️ System Info', expanded=False):
        st.write(f"**Face Detector:** {type(system.face_detector).__name__}")
        st.write(f"**Face Matcher:** {'Available' if system.face_matcher else 'Unavailable'}")
        st.write(f"**Liveness Detector:** {'Available' if system.liveness_detector else 'Unavailable'}")
        if hasattr(system, 'face_matcher') and system.face_matcher:
            st.write(f"**Known Faces:** {len(system.face_matcher.known_face_encodings)}")


def dataset_manager_ui():
    st.subheader('Dataset Manager')
    ensure_dataset_dirs()

    with st.expander('Add / Update Student', expanded=True):
        name = st.text_input('Student Name', key='add_name')
        sid = st.text_input('Student ID', key='add_id')
        up = st.file_uploader('Student Image (.jpg/.png)', type=['jpg', 'jpeg', 'png'])
        if st.button('Add/Update Student'):
            if up is None:
                st.error('Please upload an image')
            else:
                img_bytes = up.read()
                ext = os.path.splitext(up.name)[1].lower() or '.jpg'
                ok, msg = add_student(sid.strip(), name.strip(), img_bytes, ext)
                if ok:
                    st.success(f'Added/updated {name} ({sid})')
                else:
                    st.error(msg)

    with st.expander('Remove Student'):
        options = [f'{sid} - {name}' for sid, name in list_students()]
        selected = st.selectbox('Select student', options) if options else None
        if st.button('Remove Selected', disabled=not options):
            if selected:
                sid = selected.split(' - ')[0]
                ok, msg = remove_student(sid)
                if ok:
                    st.success('Removed student')
                else:
                    st.error(msg)

    # Current students table
    st.caption('Current students:')
    students = list_students()
    if students:
        st.dataframe(
            {'Student ID': [s for s, _ in students], 'Name': [n for _, n in students]},
            use_container_width=True
        )

        # Student statistics
        st.caption(f'Total students: {len(students)}')

        # Option to view student images
        if st.checkbox('Show student images'):
            cols = st.columns(3)
            for i, (student_id, student_name) in enumerate(students):
                student_dir = os.path.join(PROJECT_ROOT, 'data', 'faces', student_id)
                image_path = os.path.join(student_dir, f'{student_id}.jpg')
                if os.path.exists(image_path):
                    with cols[i % 3]:
                        st.image(image_path, caption=f'{student_name} ({student_id})',
                                width=150, use_column_width=False)
    else:
        st.info('No students in dataset yet.')

    # Logs viewer
    with st.expander('📄 Recent Logs', expanded=False):
        log_file = os.path.join(PROJECT_ROOT, 'attendance_system.log')
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    logs = f.readlines()[-20:]  # Last 20 lines
                if logs:
                    st.code(''.join(logs), language='log')
                else:
                    st.info('No logs available')
            except Exception as e:
                st.error(f'Error reading logs: {e}')
        else:
            st.info('Log file not found')


def attendance_view(system: SimpleAttendanceSystem):
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader('📹 Live Attendance Feed')
        frame_slot = st.empty()
        info_slot = st.empty()

        # Add camera controls
        if st.session_state.running:
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                if st.button('📸 Capture Frame', help='Save current frame for debugging'):
                    # This would need implementation to save the current frame
                    st.info('Frame capture not yet implemented')
            with col_b:
                if st.button('🔄 Reset View', help='Reset camera view'):
                    st.rerun()
            with col_c:
                if st.button('📊 Export Data', help='Export attendance data'):
                    # This would export the current attendance records
                    st.info('Data export not yet implemented')

    with col2:
        st.subheader('📋 Attendance Records')

        # Get all students from dataset
        students = list_students()

        if students:
            # Create attendance table
            attendance_data = []
            present_ids = set(system.attendance_records.keys())

            for student_id, student_name in students:
                if student_id in present_ids:
                    record = system.attendance_records[student_id]
                    status = "✅ Present"
                    timestamp = record['time'].strftime('%H:%M:%S')
                    confidence = f"{record['confidence']:.2f}"
                    liveness = f"{record.get('liveness_score', 1.0):.2f}"
                else:
                    # Check if session has started and time has expired
                    if (st.session_state.session_start and
                        datetime.now() - st.session_state.session_start > timedelta(minutes=st.session_state.duration_minutes)):
                        status = "❌ Absent"
                        timestamp = ""
                        confidence = ""
                        liveness = ""
                    else:
                        status = "⏳ Pending"  # Clearer status for pending
                        timestamp = ""
                        confidence = ""
                        liveness = ""

                attendance_data.append({
                    'ID': student_id,
                    'Name': student_name,
                    'Status': status,
                    'Time': timestamp,
                    'Confidence': confidence,
                    'Liveness': liveness
                })

            # Display as data table with better formatting
            if attendance_data:
                st.dataframe(
                    attendance_data,
                    use_container_width=True,
                    column_config={
                        'Status': st.column_config.TextColumn('Status', width='medium'),
                        'Confidence': st.column_config.NumberColumn('Confidence', format='%.2f'),
                        'Liveness': st.column_config.NumberColumn('Liveness', format='%.2f')
                    }
                )

                # Summary statistics
                present_count = sum(1 for record in attendance_data if 'Present' in record['Status'])
                absent_count = sum(1 for record in attendance_data if 'Absent' in record['Status'])
                pending_count = sum(1 for record in attendance_data if 'Pending' in record['Status'])

                st.markdown("---")
                col_stats1, col_stats2, col_stats3 = st.columns(3)
                col_stats1.metric("Present", present_count)
                col_stats2.metric("Absent", absent_count)
                col_stats3.metric("Pending", pending_count)
            else:
                st.info('No attendance data yet')
        else:
            st.warning('No students in dataset. Please add students first.')

        # Summary stats
        total_students = len(students) if students else 0
        present_count = len(system.attendance_records)
        absent_count = total_students - present_count

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Total Students", total_students)
        col_b.metric("Present", present_count)
        col_c.metric("Absent", absent_count)

    if st.session_state.running and system.cap is None:
        # Initialize camera when starting
        system.initialize_camera()

    # Live loop
    loops = 0
    while st.session_state.running:
        if system.cap is None:
            break
        ret, frame = system.cap.read()
        if not ret:
            info_slot.error('Camera read failed')
            break
        processed = system.process_frame(frame)
        frame_slot.image(cv2.cvtColor(processed, cv2.COLOR_BGR2RGB), channels='RGB', use_column_width=True)

        info_slot.info(f'Time left: {format_remaining()}  |  Attendance: {len(system.attendance_records)}')

        elapsed = datetime.now() - st.session_state.session_start
        if elapsed > timedelta(minutes=st.session_state.duration_minutes):
            st.session_state.running = False
            system.cleanup()
            break
        time.sleep(0.03)  # ~30 FPS
        loops += 1
        if loops % 100 == 0:
            # Allow Streamlit to handle UI events periodically
            st.rerun()

    if not st.session_state.running and system.cap:
        system.cleanup()


def seed_test_student():
    # Add the requested test student if the image exists alongside project root
    test_id = 'MH25060'
    test_name = 'Hafi'
    img_path = os.path.join(PROJECT_ROOT, 'MH25060.jpg')
    if os.path.exists(img_path):
        with open(img_path, 'rb') as f:
            add_student(test_id, test_name, f.read(), '.jpg')
        # Move the file into data/students/<id>/ and remove from root
        target_dir = os.path.join(PROJECT_ROOT, 'data', 'faces', test_id)
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, f'{test_id}.jpg')
        try:
            # Save a copy if not already there, then delete original
            if not os.path.exists(target_path):
                with open(img_path, 'rb') as src, open(target_path, 'wb') as dst:
                    dst.write(src.read())
            os.remove(img_path)
        except Exception:
            pass


def main():
    st.set_page_config(page_title=TITLE, page_icon='🎓', layout='wide')
    init_session_state()
    seed_test_student()
    draw_header()

    # Use single system instance stored in session state
    if st.session_state.system is None:
        st.session_state.system = SimpleAttendanceSystem()

    system = st.session_state.system

    side_controls(system)
    dataset_manager_ui()
    attendance_view(system)


if __name__ == '__main__':
    main()


