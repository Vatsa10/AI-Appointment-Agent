import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

class EmailHandler:
    def __init__(self):
        """Initialize email handler"""
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_address = os.getenv('EMAIL_ADDRESS', '')
        self.email_password = os.getenv('EMAIL_PASSWORD', '')
        self.business_email = os.getenv('BUSINESS_EMAIL', self.email_address)
        self.business_name = os.getenv('BUSINESS_NAME', 'Appointment Booking Service')
    
    def send_notifications(self, appointment_data):
        """Send email notifications to user and business"""
        try:
            if not self.email_address or not self.email_password:
                return {
                    'success': False,
                    'error': 'Email credentials not configured. Please set EMAIL_ADDRESS and EMAIL_PASSWORD environment variables.'
                }
            
            # Send confirmation to user
            user_result = self.send_user_confirmation(appointment_data)
            
            # Send notification to business
            business_result = self.send_business_notification(appointment_data)
            
            if user_result['success'] and business_result['success']:
                return {
                    'success': True,
                    'message': 'Email notifications sent successfully'
                }
            else:
                errors = []
                if not user_result['success']:
                    errors.append(f"User email: {user_result['error']}")
                if not business_result['success']:
                    errors.append(f"Business email: {business_result['error']}")
                
                return {
                    'success': False,
                    'error': '; '.join(errors)
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Email sending failed: {str(e)}'
            }
    
    def send_user_confirmation(self, appointment_data):
        """Send confirmation email to user"""
        try:
            user_email = appointment_data.get('email')
            if not user_email:
                return {'success': False, 'error': 'User email not provided'}
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = user_email
            msg['Subject'] = f"Appointment Confirmation - {self.business_name}"
            
            # Email body
            body = f"""
Dear {appointment_data.get('name', 'Customer')},

Thank you for booking an appointment with {self.business_name}!

Your appointment details:
• Date: {appointment_data.get('date')}
• Time: {appointment_data.get('time')}
• Service: {appointment_data.get('service')}
• Contact: {appointment_data.get('phone', 'Not provided')}

Additional Notes: {appointment_data.get('notes', 'None')}

We look forward to seeing you on your appointment date. If you need to reschedule or cancel, please contact us as soon as possible.

Best regards,
{self.business_name}

---
This is an automated message. Please do not reply to this email.
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            return self.send_email(msg)
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_business_notification(self, appointment_data):
        """Send notification email to business"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = self.business_email
            msg['Subject'] = f"New Appointment Booking - {appointment_data.get('date')} {appointment_data.get('time')}"
            
            # Email body
            body = f"""
New Appointment Booking Alert

A new appointment has been booked through the online system:

Customer Details:
• Name: {appointment_data.get('name')}
• Email: {appointment_data.get('email')}
• Phone: {appointment_data.get('phone', 'Not provided')}

Appointment Details:
• Date: {appointment_data.get('date')}
• Time: {appointment_data.get('time')}
• Service: {appointment_data.get('service')}

Additional Notes: {appointment_data.get('notes', 'None')}

Booking Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please prepare for this appointment and contact the customer if needed.

---
Automated Booking System
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            return self.send_email(msg)
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_email(self, msg):
        """Send email using SMTP"""
        try:
            # Create SMTP session
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Enable TLS encryption
            server.login(self.email_address, self.email_password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(self.email_address, msg['To'], text)
            server.quit()
            
            return {'success': True, 'message': 'Email sent successfully'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
