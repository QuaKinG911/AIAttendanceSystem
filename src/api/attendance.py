from flask import Blueprint, request, jsonify, session, g
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from src.models import db, User, AttendanceRecord, AttendanceSession, Class, Course, SessionStatus, AttendanceStatus, Enrollment
from functools import wraps
from datetime import datetime, timedelta
import cv2
import numpy as np
from src.face_detection.yolo_detector import YOLOFaceDetector
from src.face_recognition.matcher import FaceMatcher
from src.config import config

import logging

attendance_bp = Blueprint('attendance', __name__)
logger = logging.getLogger(__name__)

def session_or_jwt_required(f):
    """Decorator that allows either JWT auth or session auth"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.debug("Auth: Checking authentication")
        # Try JWT first
        if 'Authorization' in request.headers:
            try:
                verify_jwt_in_request()
                jwt_user = get_jwt_identity()
                logger.debug(f"Auth: JWT user: {jwt_user}")
                if jwt_user:
                    user = User.query.filter_by(username=jwt_user).first()
                    if user:
                        g.user = user
                        logger.debug(f"Auth: JWT auth successful for user {user.id}")
                        return f(*args, **kwargs)
            except Exception as e:
                logger.debug(f"Auth: JWT check failed: {e}")

        # Fall back to session auth
        logger.debug(f"Auth: Checking session, session keys: {list(session.keys()) if session else 'None'}")
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            logger.debug(f"Auth: Session user_id: {session.get('user_id')}, user found: {user is not None}")
            if user:
                g.user = user
                logger.debug(f"Auth: Session auth successful for user {user.id}")
                return f(*args, **kwargs)

        logger.debug("Auth: Authentication failed")
        return jsonify({'error': 'Authentication required'}), 401

    return decorated_function

# Global models
detector = None
matcher = None

def get_models():
    global detector, matcher
    if detector is None:
        detector = YOLOFaceDetector(
            confidence_threshold=config.get('detection.confidence_threshold', 0.5)
        )
    if matcher is None:
        matcher = FaceMatcher(
            tolerance=config.get('recognition.tolerance', 0.6),
            confidence_threshold=config.get('attendance.confidence_threshold', 0.7)
        )
        # Load known faces
        db_path = config.get('recognition.database_path', 'data/face_encodings.pkl')
        matcher.load_known_faces(db_path)
        logger.info(f"Loaded {len(matcher.known_face_encodings)} faces from {db_path}")
    return detector, matcher

def reload_models():
    """Force reload of AI models"""
    global detector, matcher
    detector = None
    matcher = None
    logger.info("Models cleared for reload")

# Global cache for recognition
# Format: {session_id: [{'box': [x1, y1, x2, y2], 'id': student_id, 'name': name, 'timestamp': time.time(), 'conf': conf}]}
recognition_cache = {}

def calculate_iou(box1, box2):
    """Calculate Intersection over Union between two boxes"""
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2

    x_left = max(x1_1, x1_2)
    y_top = max(y1_1, y1_2)
    x_right = min(x2_1, x2_2)
    y_bottom = min(y2_1, y2_2)

    if x_right < x_left or y_bottom < y_top:
        return 0.0

    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
    box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)

    return intersection_area / float(box1_area + box2_area - intersection_area)

@attendance_bp.route('/process-frame', methods=['POST'])
@session_or_jwt_required
def process_frame():
    try:
        # logger.debug("process_frame called") # Reduce logging
        if 'frame' not in request.files:
            return jsonify({'error': 'No frame provided'}), 400

        file = request.files['frame']
        session_id = request.form.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400

        # Read image
        filestr = file.read()
        npimg = np.frombuffer(filestr, np.uint8)
        frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        
        if frame is None:
             return jsonify({'error': 'Invalid image'}), 400

        detector, matcher = get_models()
        
        # Detect faces
        faces = detector.detect_faces_with_confidence(frame)
        # logger.debug(f"Detected {len(faces)} faces in frame")

        recognitions = []
        current_time = datetime.now().timestamp()
        
        # Initialize cache for this session if needed
        if session_id not in recognition_cache:
            recognition_cache[session_id] = []
            
        # Clean old cache entries (> 0.5 second) - Reduced from 1.0s to be more responsive
        recognition_cache[session_id] = [
            entry for entry in recognition_cache[session_id] 
            if current_time - entry['timestamp'] < 0.5
        ]
        
        new_cache_entries = []

        for (x1, y1, x2, y2, conf) in faces:
            # Check cache first
            cached_match = None
            current_box = [x1, y1, x2, y2]
            
            for entry in recognition_cache[session_id]:
                iou = calculate_iou(current_box, entry['box'])
                if iou > 0.6:  # Increased threshold to 0.6 to prevent identity swapping
                    cached_match = entry
                    break
            
            if cached_match:
                # Use cached result
                student_id = cached_match['id']
                name = cached_match['name']
                match_conf = cached_match['conf']
                # Update timestamp to keep it alive
                cached_match['timestamp'] = current_time
                cached_match['box'] = current_box # Update position
                new_cache_entries.append(cached_match)
                logger.debug(f"Recognition (cached): ID={student_id}, Name={name}, Conf={match_conf:.4f}")
            else:
                # Run recognition
                h, w = frame.shape[:2]
                # Add padding
                padding = 20
                x1_p = max(0, x1 - padding)
                y1_p = max(0, y1 - padding)
                x2_p = min(w, x2 + padding)
                y2_p = min(h, y2 + padding)
                
                face_img = frame[y1_p:y2_p, x1_p:x2_p]
                
                if face_img.size == 0:
                    continue
                    
                face_encoding = matcher.extract_face_features(face_img)
                if face_encoding is None:
                    logger.debug("Failed to extract features from face")
                    continue
                
                logger.debug(f"Extracted encoding shape: {face_encoding.shape}")
                    
                student_id, name, match_conf = matcher.recognize_face(face_encoding)
                logger.debug(f"Recognition: ID={student_id}, Name={name}, Conf={match_conf:.4f}")
                
                # Double check confidence against config
                min_conf = config.get('attendance.confidence_threshold', 0.75)
                if match_conf < min_conf:
                    logger.info(f"Rejected low confidence match: {name} ({match_conf:.4f} < {min_conf})")
                    student_id = None
                    name = None
                
                # Only cache if we actually recognized someone
                # This prevents "Unknown" from sticking and forcing re-check
                if student_id:
                    new_entry = {
                        'box': current_box,
                        'id': student_id,
                        'name': name,
                        'conf': match_conf,
                        'timestamp': current_time
                    }
                    new_cache_entries.append(new_entry)
            
            status = 'unknown'
            
            if name and student_id:
                # Record attendance
                # Check if already recorded for this session
                existing = AttendanceRecord.query.filter_by(
                    session_id=session_id, 
                    student_id=student_id
                ).first()
                
                if not existing:
                    # Determine status based on time
                    session_obj = AttendanceSession.query.get(session_id)
                    now = datetime.now()
                    
                    # Calculate time difference in minutes
                    start_time = session_obj.start_time
                    if isinstance(start_time, str):
                         start_time = datetime.fromisoformat(start_time)
                         
                    elapsed_minutes = (now - start_time).total_seconds() / 60.0
                    
                    new_status = AttendanceStatus.ABSENT # Default
                    
                    if elapsed_minutes <= session_obj.present_window_minutes:
                        new_status = AttendanceStatus.PRESENT
                    elif elapsed_minutes <= (session_obj.present_window_minutes + session_obj.late_window_minutes):
                        new_status = AttendanceStatus.LATE
                    else:
                        # Outside of both windows, but detected. 
                        # If we want to allow marking late even after window, keep LATE.
                        # Or if strict, keep ABSENT (but that means they are detected but ignored?)
                        # User request: "after the late window end all the rest of the students should be absent"
                        # This implies that if they are detected AFTER late window, they should NOT be marked present/late?
                        # But if they are physically there, maybe just mark LATE?
                        # Let's stick to LATE for now if detected, but maybe flag it?
                        # Actually, user said: "after the late window end all the rest of the students should be absent"
                        # This usually refers to the *final* status of those who *never* showed up.
                        # If someone shows up 2 hours late, are they absent? Usually yes.
                        # Let's mark as LATE but maybe with a note? Or just ignore?
                        # Let's assume strict windows:
                        new_status = AttendanceStatus.ABSENT
                        logger.info(f"Student {name} detected but outside late window ({elapsed_minutes:.1f} min)")

                    if new_status != AttendanceStatus.ABSENT:
                        record = AttendanceRecord(
                            session_id=session_id,
                            student_id=student_id,
                            status=new_status,
                            detected_at=now,
                            confidence_score=match_conf
                        )
                        db.session.add(record)
                        db.session.commit()
                        status = new_status.value
                        logger.info(f"Marked {name} as {status} (elapsed: {elapsed_minutes:.1f} min)")
                    else:
                         status = 'absent' # Detected but too late
                else:
                    status = existing.status.value
            
            recognitions.append({
                'bounding_box': [int(x1), int(y1), int(x2), int(y2)],
                'student_id': student_id,
                'student_name': name,
                'confidence': int(match_conf * 100),
                'status': status,
                'frame_width': frame.shape[1],
                'frame_height': frame.shape[0]
            })
            
        # Update global cache
        recognition_cache[session_id] = new_cache_entries
            
        return jsonify({
            'success': True,
            'recognitions': recognitions
        })

    except Exception as e:
        logger.error(f"Error in process_frame: {e}")
        return jsonify({'error': str(e)}), 500



@attendance_bp.route('/sessions', methods=['GET'])
@session_or_jwt_required
def get_sessions():
    """Get attendance sessions"""
    user = g.user
    
    try:
        query = AttendanceSession.query
        
        # If teacher, filter by classes they teach
        if user.role.value == 'teacher':
            # Find classes where this user is a teacher
            # This is a bit complex because teacher assignment is in Course, not Class directly
            # But we can find courses taught by this teacher and get their class_ids
            teacher_courses = Course.query.filter_by(teacher_id=user.id).all()
            class_ids = [c.class_id for c in teacher_courses]
            query = query.filter(AttendanceSession.class_id.in_(class_ids))
            
        sessions = query.order_by(AttendanceSession.start_time.desc()).all()
        
        result = []
        for s in sessions:
            class_obj = Class.query.get(s.class_id)
            recorded_count = AttendanceRecord.query.filter_by(session_id=s.id).count()
            
            result.append({
                'id': s.id,
                'class_name': class_obj.name if class_obj else 'Unknown',
                'session_date': s.session_date.isoformat(),
                'start_time': s.start_time.isoformat(),
                'end_time': s.end_time.isoformat() if s.end_time else None,
                'status': s.status.value,
                'recorded_count': recorded_count
            })
            
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/sessions', methods=['POST'])
@session_or_jwt_required
def create_session():
    """Start a new attendance session"""
    try:
        data = request.get_json()
        class_id = data.get('class_id')
        
        if not class_id:
            return jsonify({'error': 'Class ID is required'}), 400
            
        session_duration = data.get('session_duration')
        auto_end_time_input = data.get('auto_end_time')
        auto_end_time = None

        if session_duration:
            try:
                duration_minutes = int(session_duration)
                start_dt = datetime.now()
                end_dt = start_dt + timedelta(minutes=duration_minutes)
                auto_end_time = end_dt.time()
            except (ValueError, TypeError):
                pass
        elif auto_end_time_input:
            try:
                # Parse time string like "14:30"
                auto_end_time = datetime.strptime(auto_end_time_input, '%H:%M').time()
            except (ValueError, TypeError):
                pass 

        # Create new session
        new_session = AttendanceSession(
            class_id=class_id,
            session_date=datetime.now().date(),
            start_time=datetime.now(),
            status=SessionStatus.ACTIVE,
            present_window_minutes=data.get('present_window', 5),
            late_window_minutes=data.get('late_window', 15),
            auto_end_time=auto_end_time
        )
        
        db.session.add(new_session)
        db.session.commit()
        
        logger.info(f"Session started: {new_session.id} for class {class_id}")

        return jsonify({
            'success': True,
            'message': 'Session started',
            'session_id': new_session.id,
            'auto_end_time': str(new_session.auto_end_time) if new_session.auto_end_time else None
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating session: {e}")
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/sessions/<int:session_id>', methods=['PUT', 'DELETE'])
@session_or_jwt_required
def update_session(session_id):
    """Update or delete session"""
    logger.info(f"update_session called with session_id={session_id}, method={request.method}")
    
    if request.method == 'DELETE':
        try:
            session_obj = AttendanceSession.query.get_or_404(session_id)
            # Delete associated records first
            AttendanceRecord.query.filter_by(session_id=session_id).delete()
            db.session.delete(session_obj)
            db.session.commit()
            logger.info(f"Session {session_id} deleted")
            return jsonify({'success': True, 'message': 'Session deleted'})
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

    try:
        session_obj = AttendanceSession.query.get_or_404(session_id)
        logger.debug(f"Found session {session_id}, current status: {session_obj.status}")
        data = request.get_json()
        logger.debug(f"Request data: {data}")

        if 'status' in data:
            if data['status'] == 'completed':
                # Check if already completed
                if session_obj.status == SessionStatus.COMPLETED:
                    logger.info(f"Session {session_id} already completed")
                    return jsonify({'success': True, 'message': 'Session already completed'})
                logger.info(f"Completing session {session_id}")
                session_obj.status = SessionStatus.COMPLETED
                session_obj.end_time = datetime.now()
            else:
                session_obj.status = SessionStatus(data['status'])

        db.session.commit()
        logger.info(f"Session {session_id} updated successfully")
        return jsonify({'success': True, 'message': 'Session updated'})
    except Exception as e:
        logger.error(f"Error updating session {session_id}: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@attendance_bp.route('/sessions/<int:session_id>/records', methods=['GET', 'POST'])
@session_or_jwt_required
def manage_session_records(session_id):
    """Get all records for a session (including absent students) or create a new record"""
    try:
        session_obj = AttendanceSession.query.get_or_404(session_id)
        
        if request.method == 'POST':
            # Create a new record manually
            data = request.get_json()
            student_id = data.get('student_id')
            status = data.get('status')
            override_reason = data.get('override_reason')
            
            if not student_id or not status:
                return jsonify({'error': 'Missing student_id or status'}), 400
                
            # Check if record already exists
            existing_record = AttendanceRecord.query.filter_by(
                session_id=session_id, 
                student_id=student_id
            ).first()
            
            if existing_record:
                return jsonify({'error': 'Record already exists for this student'}), 400
                
            new_record = AttendanceRecord(
                session_id=session_id,
                student_id=student_id,
                status=AttendanceStatus(status),
                manual_override=True,
                override_by=g.user.id,
                override_reason=override_reason,
                detected_at=datetime.now()
            )
            db.session.add(new_record)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Record created', 'id': new_record.id})

        # GET: Fetch all students in the class and their attendance status
        # 1. Get all students enrolled in the class
        enrolled_students = db.session.query(User).join(Enrollment).filter(
            Enrollment.class_id == session_obj.class_id
        ).all()
        logger.info(f"Found {len(enrolled_students)} enrolled students for class {session_obj.class_id}")
        
        # 2. Get existing records for this session
        existing_records = AttendanceRecord.query.filter_by(session_id=session_id).all()
        logger.info(f"Found {len(existing_records)} attendance records for session {session_id}")
        
        records_map = {r.student_id: r for r in existing_records}
        
        result = []
        for student in enrolled_students:
            record = records_map.get(student.id)
            
            result.append({
                'id': record.id if record else None,
                'student_id': student.id,
                'student_name': student.full_name or student.username,
                'student_email': student.email,
                'status': record.status.value if record else 'absent', # Default to absent
                'check_in_time': record.detected_at.isoformat() if record and record.detected_at else None,
                'confidence_score': float(record.confidence_score) if record and record.confidence_score else None,
                'override_reason': record.override_reason if record else None
            })
            
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in manage_session_records: {e}")
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/records/<int:record_id>', methods=['GET', 'PUT'])
@session_or_jwt_required
def manage_record(record_id):
    """Get or update a specific attendance record"""
    try:
        record = AttendanceRecord.query.get_or_404(record_id)
        
        if request.method == 'GET':
            return jsonify({
                'id': record.id,
                'status': record.status.value,
                'override_reason': record.override_reason
            })
            
        elif request.method == 'PUT':
            data = request.get_json()
            if 'status' in data:
                record.status = AttendanceStatus(data['status'])
            if 'override_reason' in data:
                record.override_reason = data['override_reason']
                record.manual_override = True
                record.override_by = g.user.id
                
            db.session.commit()
            return jsonify({'message': 'Record updated'})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/recent', methods=['GET'])
@session_or_jwt_required
def get_recent_attendance():
    """Get recent attendance records for current user"""
    user = g.user

    # Get recent attendance records (last 10)
    records = AttendanceRecord.query.filter_by(student_id=user.id)\
        .join(AttendanceSession)\
        .order_by(AttendanceRecord.detected_at.desc())\
        .limit(10)\
        .all()

    result = []
    for record in records:
        # Get class and course info
        session_obj = record.session
        class_obj = Class.query.get(session_obj.class_id)

        result.append({
            'date': record.detected_at.strftime('%Y-%m-%d') if record.detected_at else 'N/A',
            'time': record.detected_at.strftime('%H:%M') if record.detected_at else 'N/A',
            'class_name': class_obj.name if class_obj else 'Unknown Class',
            'status': record.status.value,
            'confidence': float(record.confidence_score) if record.confidence_score else None
        })

    return jsonify(result)