# src/email_service.py - Email notification service

import os
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.api_key = os.getenv('SENDGRID_API_KEY')
        self.from_email = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@school.edu')
        self.client = SendGridAPIClient(self.api_key) if self.api_key else None

    def send_email(self, to_email, subject, html_content, text_content=None):
        """Send an email using SendGrid"""
        if not self.client:
            logger.warning("SendGrid not configured, skipping email send")
            return False

        try:
            from_email = Email(self.from_email)
            to_email = To(to_email)
            content = Content("text/html", html_content)

            mail = Mail(from_email, to_email, subject, content)

            if text_content:
                mail.add_content(Content("text/plain", text_content))

            response = self.client.send(mail)
            logger.info(f"Email sent successfully to {to_email} with status {response.status_code}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_attendance_notification(self, parent_email, student_name, attendance_data):
        """Send attendance notification to parent"""
        subject = f"Attendance Update for {student_name}"

        html_content = f"""
        <html>
        <body>
            <h2>Attendance Notification</h2>
            <p>Dear Parent/Guardian,</p>
            <p>This is an automated notification regarding your child's attendance:</p>

            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>Student: {student_name}</h3>
                <p><strong>Attendance Rate:</strong> {attendance_data.get('attendance_rate', 'N/A')}%</p>
                <p><strong>Recent Status:</strong> {attendance_data.get('recent_status', 'N/A')}</p>
                <p><strong>Date:</strong> {attendance_data.get('date', 'N/A')}</p>
            </div>

            <p>Please log in to the parent portal for detailed attendance information.</p>

            <p>Best regards,<br>School Attendance System</p>
        </body>
        </html>
        """

        return self.send_email(parent_email, subject, html_content)

    def send_absence_alert(self, parent_email, student_name, absence_details):
        """Send absence alert to parent"""
        subject = f"Absence Alert for {student_name}"

        html_content = f"""
        <html>
        <body>
            <h2>Absence Alert</h2>
            <p>Dear Parent/Guardian,</p>
            <p>This is an important notification regarding your child's absence:</p>

            <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="color: #856404;">Student: {student_name}</h3>
                <p><strong>Date:</strong> {absence_details.get('date', 'N/A')}</p>
                <p><strong>Course:</strong> {absence_details.get('course', 'N/A')}</p>
                <p><strong>Time:</strong> {absence_details.get('time', 'N/A')}</p>
            </div>

            <p>If this absence was excused, please submit an excuse through the parent portal.</p>
            <p>For unexcused absences, please contact the school administration.</p>

            <p>Best regards,<br>School Attendance System</p>
        </body>
        </html>
        """

        return self.send_email(parent_email, subject, html_content)

    def send_weekly_report(self, parent_email, student_name, weekly_data):
        """Send weekly attendance report"""
        subject = f"Weekly Attendance Report for {student_name}"

        # Build attendance summary
        attendance_summary = ""
        for day, status in weekly_data.get('daily_attendance', {}).items():
            status_badge = {
                'present': '<span style="color: green;">✓ Present</span>',
                'late': '<span style="color: orange;">⚠ Late</span>',
                'absent': '<span style="color: red;">✗ Absent</span>'
            }.get(status, status)
            attendance_summary += f"<tr><td>{day}</td><td>{status_badge}</td></tr>"

        html_content = f"""
        <html>
        <body>
            <h2>Weekly Attendance Report</h2>
            <p>Dear Parent/Guardian,</p>
            <p>Here is the attendance summary for {student_name} this week:</p>

            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>Weekly Summary</h3>
                <p><strong>Attendance Rate:</strong> {weekly_data.get('attendance_rate', 'N/A')}%</p>
                <p><strong>Days Present:</strong> {weekly_data.get('days_present', 0)}</p>
                <p><strong>Days Late:</strong> {weekly_data.get('days_late', 0)}</p>
                <p><strong>Days Absent:</strong> {weekly_data.get('days_absent', 0)}</p>
            </div>

            <h3>Daily Attendance</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background-color: #e9ecef;">
                        <th style="border: 1px solid #dee2e6; padding: 8px;">Day</th>
                        <th style="border: 1px solid #dee2e6; padding: 8px;">Status</th>
                    </tr>
                </thead>
                <tbody>
                    {attendance_summary}
                </tbody>
            </table>

            <p>Please log in to the parent portal for more detailed information.</p>

            <p>Best regards,<br>School Attendance System</p>
        </body>
        </html>
        """

        return self.send_email(parent_email, subject, html_content)

    def send_appeal_response(self, parent_email, student_name, appeal_data):
        """Send appeal response to parent"""
        subject = f"Attendance Appeal Response for {student_name}"

        status_color = "green" if appeal_data.get('approved') else "red"
        status_text = "Approved" if appeal_data.get('approved') else "Denied"

        html_content = f"""
        <html>
        <body>
            <h2>Attendance Appeal Response</h2>
            <p>Dear Parent/Guardian,</p>
            <p>Your attendance appeal for {student_name} has been reviewed:</p>

            <div style="background-color: #f8f9fa; border-left: 4px solid {status_color}; padding: 15px; margin: 20px 0;">
                <h3 style="color: {status_color};">Appeal {status_text}</h3>
                <p><strong>Date:</strong> {appeal_data.get('date', 'N/A')}</p>
                <p><strong>Original Status:</strong> {appeal_data.get('original_status', 'N/A')}</p>
                <p><strong>New Status:</strong> {appeal_data.get('new_status', 'N/A')}</p>
                <p><strong>Reason:</strong> {appeal_data.get('reason', 'N/A')}</p>
                {f"<p><strong>Review Notes:</strong> {appeal_data.get('notes', '')}</p>" if appeal_data.get('notes') else ""}
            </div>

            <p>If you have any questions, please contact the school administration.</p>

            <p>Best regards,<br>School Attendance System</p>
        </body>
        </html>
        """

        return self.send_email(parent_email, subject, html_content)

    def send_ml_anomaly_alert(self, admin_email, anomaly_details):
        """Send ML anomaly detection alert to admin"""
        subject = f"🚨 Attendance Anomaly Alert: {anomaly_details['anomaly_type'].replace('_', ' ').title()}"

        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
                .alert-box {{ border-left: 4px solid #dc3545; background-color: #f8d7da; padding: 15px; margin: 20px 0; }}
                .metrics {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🤖 AI Attendance System Alert</h2>
                    <p>Machine Learning Anomaly Detected</p>
                </div>

                <div class="alert-box">
                    <h3>⚠️ {anomaly_details['anomaly_type'].replace('_', ' ').title()}</h3>
                    <p><strong>Student ID:</strong> {anomaly_details['student_id']}</p>
                    <p><strong>Severity:</strong> <span style="color: {anomaly_details['severity'] == 'high' and '#dc3545' or '#ffc107'};">{anomaly_details['severity'].upper()}</span></p>
                    <p><strong>Description:</strong> {anomaly_details['description']}</p>
                </div>

                <div class="metrics">
                    <h4>📊 Detection Details</h4>
                    <p><strong>Detected At:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Confidence Score:</strong> {anomaly_details.get('confidence', 'N/A')}</p>
                    {f"<p><strong>Affected Dates:</strong> {', '.join(anomaly_details['dates']) if anomaly_details.get('dates') else 'N/A'}</p>" if anomaly_details.get('dates') else ""}
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{os.getenv('APP_URL', 'http://localhost:5000')}/admin/ml-insights"
                       style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        🔍 Review in Dashboard
                    </a>
                </div>

                <div class="footer">
                    <p>This alert was generated by the AI Attendance System's machine learning engine.</p>
                    <p>Please review the student's attendance pattern and consider appropriate interventions.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(admin_email, subject, html_content)

    def send_ml_prediction_alert(self, admin_email, prediction_details):
        """Send ML prediction alert for high-risk students"""
        subject = f"🎯 High-Risk Student Alert: Student {prediction_details['student_id']}"

        risk_color = {'high': '#dc3545', 'medium': '#ffc107', 'low': '#28a745'}[prediction_details.get('risk_level', 'low')]

        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
                .risk-box {{ border-left: 4px solid {risk_color}; background-color: #f8f9fa; padding: 15px; margin: 20px 0; }}
                .metrics {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .recommendations {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🎯 AI Risk Assessment Alert</h2>
                    <p>High-Risk Student Identified</p>
                </div>

                <div class="risk-box">
                    <h3 style="color: {risk_color};">{prediction_details['risk_level'].upper()} RISK STUDENT</h3>
                    <p><strong>Student ID:</strong> {prediction_details['student_id']}</p>
                    <p><strong>Risk Level:</strong> <span style="color: {risk_color}; font-weight: bold;">{prediction_details['risk_level'].title()}</span></p>
                    <p><strong>Confidence:</strong> {(prediction_details.get('confidence', 0) * 100):.1f}%</p>
                    <p><strong>Attendance Rate:</strong> {(prediction_details.get('attendance_rate', 0) * 100):.1f}%</p>
                </div>

                <div class="recommendations">
                    <h4>💡 Recommended Actions</h4>
                    <ul>
                        {''.join(f'<li>{rec}</li>' for rec in prediction_details.get('recommendations', []))}
                    </ul>
                </div>

                <div class="metrics">
                    <h4>📊 Risk Assessment Details</h4>
                    <p><strong>Assessment Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Prediction Model:</strong> Random Forest Ensemble</p>
                    <p><strong>Features Analyzed:</strong> Attendance patterns, trends, streaks, volatility</p>
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{os.getenv('APP_URL', 'http://localhost:5000')}/admin/ml-insights"
                       style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        📊 View Full Analysis
                    </a>
                </div>

                <div class="footer">
                    <p>This alert was generated by the AI Attendance System's predictive analytics engine.</p>
                    <p>Early intervention can significantly improve student outcomes.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(admin_email, subject, html_content)

# Global email service instance
email_service = EmailService()