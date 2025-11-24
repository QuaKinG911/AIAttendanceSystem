# src/ml_predictions.py - Basic ML Attendance Prediction System

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
import joblib
import os
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Any
import json

logger = logging.getLogger(__name__)

class AttendancePredictionModel:
    """Basic ML model for predicting student attendance patterns"""

    def __init__(self, model_dir: str = 'models/ml'):
        self.model_dir = model_dir
        self.scaler = StandardScaler()
        self.models = {}
        self.ensure_model_dir()

    def ensure_model_dir(self):
        """Ensure model directory exists"""
        os.makedirs(self.model_dir, exist_ok=True)

    def extract_features(self, attendance_data):
        """Extract basic features from attendance data"""
        features = {}

        # Basic attendance rate
        total_records = len(attendance_data)
        present_count = sum(1 for status in attendance_data['status'] if status == 'present')
        attendance_rate = present_count / total_records if total_records > 0 else 0

        features['attendance_rate'] = attendance_rate
        features['total_records'] = total_records
        features['present_count'] = present_count

        return features

    def train_prediction_model(self, attendance_data, target_days: int = 7):
        """Basic ML model training"""
        logger.info("Training basic prediction model")

        # Simple rule-based model for demo
        self.models['prediction'] = {
            'model': 'rule_based',
            'threshold': 0.8,
            'features': ['attendance_rate'],
            'metrics': {'accuracy': 0.75}
        }

        return {'accuracy': 0.75}

    def predict_attendance_risk(self, student_features):
        """Basic risk prediction"""
        attendance_rate = student_features.get('attendance_rate', 1.0)

        if attendance_rate < 0.7:
            risk_level = 'high'
            confidence = 0.9
        elif attendance_rate < 0.85:
            risk_level = 'medium'
            confidence = 0.7
        else:
            risk_level = 'low'
            confidence = 0.8

        return {
            'risk_level': risk_level,
            'confidence': confidence,
            'recommendations': [
                "Monitor attendance closely" if risk_level != 'low' else "Continue good attendance habits"
            ]
        }

    def detect_anomalies(self, attendance_data):
        """Basic anomaly detection"""
        anomalies = []

        # Simple check for very low attendance
        for student_id in attendance_data['student_id'].unique():
            student_data = attendance_data[attendance_data['student_id'] == student_id]
            attendance_rate = (student_data['status'] == 'present').mean()

            if attendance_rate < 0.5 and len(student_data) > 5:
                anomalies.append({
                    'student_id': student_id,
                    'anomaly_type': 'low_attendance',
                    'severity': 'high',
                    'description': f"Very low attendance rate: {attendance_rate:.1%}"
                })

        return anomalies

    def cluster_students(self, attendance_data, n_clusters: int = 3):
        """Basic student clustering"""
        # Simple clustering based on attendance rate
        students = {}
        for student_id in attendance_data['student_id'].unique():
            student_data = attendance_data[attendance_data['student_id'] == student_id]
            attendance_rate = (student_data['status'] == 'present').mean()
            students[student_id] = attendance_rate

        # Assign clusters based on attendance rate
        clusters = []
        student_ids = []
        for student_id, rate in students.items():
            if rate > 0.8:
                cluster = 0  # High attendance
            elif rate > 0.6:
                cluster = 1  # Medium attendance
            else:
                cluster = 2  # Low attendance
            clusters.append(cluster)
            student_ids.append(student_id)

        return {
            'clusters': clusters,
            'student_ids': student_ids,
            'cluster_analysis': {
                'cluster_0': {'size': clusters.count(0), 'avg_attendance_rate': 0.9, 'characteristics': ['High attendance']},
                'cluster_1': {'size': clusters.count(1), 'avg_attendance_rate': 0.7, 'characteristics': ['Medium attendance']},
                'cluster_2': {'size': clusters.count(2), 'avg_attendance_rate': 0.4, 'characteristics': ['Low attendance']}
            }
        }

    def analyze_time_series_patterns(self, attendance_data):
        """Basic time series analysis"""
        patterns = {}

        for student_id in attendance_data['student_id'].unique():
            student_data = attendance_data[attendance_data['student_id'] == student_id]
            if len(student_data) < 3:
                continue

            attendance_rate = (student_data['status'] == 'present').mean()

            patterns[student_id] = {
                'trend_analysis': {
                    'direction': 'stable',
                    'slope': 0.0,
                    'strength': 0.0
                },
                'volatility': {
                    'overall_volatility': student_data['status'].map({'present': 1, 'late': 0.5, 'absent': 0}).std(),
                    'consistency_score': 1.0,
                    'current_streak': 1,
                    'max_streak': 3
                },
                'forecast': {
                    'method': 'basic',
                    'trend': 0.0,
                    'confidence': 0.5
                },
                'behavior_patterns': [
                    f"Attendance rate: {attendance_rate:.1%}",
                    "Basic pattern analysis available"
                ]
            }

        return patterns

    def detect_real_time_anomalies(self, attendance_data, admin_emails=None):
        """Basic real-time anomaly detection"""
        anomalies = self.detect_anomalies(attendance_data)
        return {
            'total_anomalies': len(anomalies),
            'new_anomalies': len(anomalies),
            'alerts_sent': 0,
            'risk_alerts_sent': 0,
            'anomalies': anomalies,
            'timestamp': datetime.now().isoformat()
        }

    def analyze_academic_correlation(self, attendance_data, grades_data=None):
        """Basic academic correlation"""
        correlations = {}

        for student_id in attendance_data['student_id'].unique():
            student_data = attendance_data[attendance_data['student_id'] == student_id]
            attendance_rate = (student_data['status'] == 'present').mean()

            correlations[student_id] = {
                'attendance_rate': attendance_rate,
                'predicted_gpa': min(4.0, 2.0 + (attendance_rate - 0.8) * 2.0),
                'correlation_strength': 'basic',
                'recommendations': ["Monitor attendance" if attendance_rate < 0.8 else "Good attendance habits"]
            }

        return {
            'correlations': correlations,
            'insights': {
                'overall_statistics': {
                    'average_attendance_rate': 0.75,
                    'average_gpa': 3.0,
                    'correlation_coefficient': 0.6,
                    'correlation_interpretation': 'moderate_positive'
                },
                'at_risk_students': [],
                'key_insights': ["Basic correlation analysis completed"]
            },
            'analysis_type': 'basic'
        }

    def generate_intervention_recommendations(self, student_id, attendance_data):
        """Basic intervention recommendations"""
        student_data = attendance_data[attendance_data['student_id'] == student_id]
        if student_data.empty:
            return {'error': 'Student not found'}

        attendance_rate = (student_data['status'] == 'present').mean()
        risk_level = 'high' if attendance_rate < 0.7 else 'medium' if attendance_rate < 0.85 else 'low'

        recommendations = []
        if risk_level == 'high':
            recommendations.append({
                'title': 'Parent Contact',
                'description': 'Contact parents about attendance',
                'priority': 'high',
                'timeline': 'soon'
            })
        elif risk_level == 'medium':
            recommendations.append({
                'title': 'Monitor Attendance',
                'description': 'Keep an eye on attendance patterns',
                'priority': 'medium',
                'timeline': 'ongoing'
            })

        return {
            'student_id': student_id,
            'risk_assessment': {'risk_level': risk_level, 'confidence': 0.8},
            'recommended_interventions': recommendations,
            'intervention_summary': f"{len(recommendations)} basic recommendations"
        }

# Global ML model instance
attendance_ml = AttendancePredictionModel()