import gspread
from google.oauth2.service_account import Credentials
import json
import os
from datetime import datetime

class GoogleSheetsHandler:
    def __init__(self):
        """Initialize Google Sheets handler"""
        self.client = None
        self.sheet = None
        self.setup_client()
    
    def setup_client(self):
        """Setup Google Sheets client with authentication"""
        try:
            # Get credentials from environment variable
            creds_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
            spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
            
            if not creds_json:
                raise ValueError("GOOGLE_SHEETS_CREDENTIALS not found in environment variables")
                
            if not spreadsheet_id:
                raise ValueError("GOOGLE_SPREADSHEET_ID not found in environment variables")
            
            # Parse the JSON string from environment variable
            try:
                creds_dict = json.loads(creds_json)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in GOOGLE_SHEETS_CREDENTIALS: {str(e)}")
            
            # Define the scope
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Create credentials
            credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
            
            # Initialize client
            self.client = gspread.authorize(credentials)
            
            # Open the spreadsheet
            self.sheet = self.client.open_by_key(spreadsheet_id).sheet1
            
            # Ensure headers exist
            self.ensure_headers()
            
        except Exception as e:
            print(f"Error setting up Google Sheets client: {str(e)}")
            self.client = None
            self.sheet = None
            raise
    
    def ensure_headers(self):
        """Ensure the spreadsheet has proper headers"""
        try:
            if not self.sheet:
                return
                
            headers = [
                'Timestamp',
                'Name',
                'Email',
                'Phone',
                'Date',
                'Time',
                'Service',
                'Notes',
                'Status'
            ]
            
            # Check if first row has headers
            first_row = self.sheet.row_values(1)
            
            if not first_row or first_row != headers:
                # Insert headers
                self.sheet.insert_row(headers, 1)
                
        except Exception as e:
            print(f"Error ensuring headers: {str(e)}")
    
    def add_appointment(self, appointment_data):
        """Add appointment to Google Sheets"""
        try:
            if not self.sheet:
                return {
                    'success': False,
                    'error': 'Google Sheets not properly configured. Please check your credentials and spreadsheet ID.'
                }
            
            # Prepare row data
            row_data = [
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # Timestamp
                appointment_data.get('name', ''),
                appointment_data.get('email', ''),
                appointment_data.get('phone', ''),
                appointment_data.get('date', ''),
                appointment_data.get('time', ''),
                appointment_data.get('service', ''),
                appointment_data.get('notes', ''),
                'Confirmed'
            ]
            
            # Add row to sheet
            self.sheet.append_row(row_data)
            
            return {
                'success': True,
                'message': 'Appointment added successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to add appointment to Google Sheets: {str(e)}'
            }
    
    def get_available_slots(self, date):
        """Get available time slots for a given date"""
        try:
            if not self.sheet:
                return []
            
            # Get all records
            records = self.sheet.get_all_records()
            
            # Find booked slots for the date
            booked_slots = []
            for record in records:
                if record.get('Date') == date and record.get('Status') == 'Confirmed':
                    booked_slots.append(record.get('Time'))
            
            # Define all possible slots (9 AM to 5 PM, hourly)
            all_slots = [
                '09:00', '10:00', '11:00', '12:00',
                '13:00', '14:00', '15:00', '16:00', '17:00'
            ]
            
            # Return available slots
            available_slots = [slot for slot in all_slots if slot not in booked_slots]
            return available_slots
            
        except Exception as e:
            print(f"Error getting available slots: {str(e)}")
            return []
    
    def is_slot_available(self, date, time):
        """Check if a specific slot is available"""
        try:
            available_slots = self.get_available_slots(date)
            return time in available_slots
        except Exception as e:
            print(f"Error checking slot availability: {str(e)}")
            return True  # Assume available if error occurs
