# src/analytics/__init__.py - Analytics functions

import redis
from datetime import datetime, timedelta
from sqlalchemy import func
from src.models import db, AttendanceRecord, AttendanceSession, Class, User

# Redis connection
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_live_attendance_stats(class_id=None, hours=24):
    """Get live attendance statistics"""
    cache_key = f"attendance_stats:{class_id or 'global'}:{hours}"

    # Try cache first
    cached = redis_client.get(cache_key)
    if cached:
        return eval(cached.decode())  # In production, use JSON

    # Calculate stats
    start_time = datetime.now() - timedelta(hours=hours)

    query = db.session.query(
        AttendanceRecord.status,
        func.count(AttendanceRecord.id).label('count')
    ).join(AttendanceSession).filter(
        AttendanceSession.start_time >= start_time
    )

    if class_id:
        query = query.filter(AttendanceSession.class_id == class_id)

    stats = query.group_by(AttendanceRecord.status).all()

    result = {status.value: count for status, count in stats}

    # Cache for 5 minutes
    redis_client.setex(cache_key, 300, str(result))

    return result

def get_attendance_trends(days=30):
    """Get attendance trends over time"""
    start_date = datetime.now() - timedelta(days=days)

    sessions = AttendanceSession.query.filter(
        AttendanceSession.session_date >= start_date.date()
    ).order_by(AttendanceSession.session_date).all()

    trends = []
    for session in sessions:
        records = AttendanceRecord.query.filter_by(session_id=session.id).all()
        present = len([r for r in records if r.status.name == 'PRESENT'])
        late = len([r for r in records if r.status.name == 'LATE'])
        absent = len([r for r in records if r.status.name == 'ABSENT'])

        trends.append({
            'date': session.session_date.isoformat(),
            'present': present,
            'late': late,
            'absent': absent,
            'total': present + late + absent
        })

    return trends

def get_student_performance(student_id, days=90):
    """Get individual student performance"""
    start_date = datetime.now() - timedelta(days=days)

    records = AttendanceRecord.query.filter(
        AttendanceRecord.student_id == student_id
    ).join(AttendanceSession).filter(
        AttendanceSession.session_date >= start_date.date()
    ).all()

    total_sessions = len(records)
    present_count = len([r for r in records if r.status.name == 'PRESENT'])
    late_count = len([r for r in records if r.status.name == 'LATE'])

    return {
        'total_sessions': total_sessions,
        'present_count': present_count,
        'late_count': late_count,
        'absent_count': total_sessions - present_count - late_count,
        'attendance_rate': round((present_count + late_count) / max(total_sessions, 1) * 100, 2)
    }

def detect_anomalies():
    """Detect unusual attendance patterns"""
    # Simple anomaly detection - can be enhanced with ML
    today = datetime.now().date()

    # Check for classes with unusually low attendance
    sessions_today = AttendanceSession.query.filter_by(session_date=today).all()

    anomalies = []
    for session in sessions_today:
        records = AttendanceRecord.query.filter_by(session_id=session.id).all()
        present_rate = len([r for r in records if r.status.name in ['PRESENT', 'LATE']]) / max(len(records), 1)

        if present_rate < 0.5:  # Less than 50% attendance
            anomalies.append({
                'type': 'low_attendance',
                'class_id': session.class_id,
                'session_id': session.id,
                'rate': round(present_rate * 100, 2)
            })

    return anomalies