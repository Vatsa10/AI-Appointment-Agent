import os
import json
import re
from datetime import datetime, timedelta
from google import genai
from google.genai import types

class ChatbotHandler:
    def __init__(self):
        """Initialize AI chatbot handler"""
        api_key = os.getenv("GENAI_API_KEY")
        if not api_key:
            raise ValueError("GENAI_API_KEY environment variable is not set")
            
        self.client = genai.Client(api_key=api_key)
        self.services = [
            "Consultation",
            "Medical Check-up", 
            "Dental Cleaning",
            "Physical Therapy",
            "Vaccination",
            "Blood Test",
            "X-Ray",
            "Other"
        ]
        
        # Get current date for AI context
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_day = datetime.now().strftime('%A, %B %d, %Y')
        
        self.system_prompt = f"""You are an AI appointment booking assistant. Your job is to help users book appointments through a conversational interface.

CURRENT DATE AND TIME: Today is {current_day} ({current_date})

APPOINTMENT REQUIREMENTS:
- Name (required)
- Email (valid format required)
- Phone (10-15 digits required)
- Service type (from available services or custom)
- Date (must be future date, within 6 months from today {current_date})
- Time (9 AM to 5 PM, hourly slots)
- Notes (optional)

AVAILABLE SERVICES: Consultation, Medical Check-up, Dental Cleaning, Physical Therapy, Vaccination, Blood Test, X-Ray, Other

CONVERSATION FLOW:
1. Greet user and start collecting information
2. Guide them through providing all required details
3. Validate each piece of information
4. Show summary and ask for confirmation
5. Once confirmed, indicate booking is complete

IMPORTANT RULES:
- Be friendly and conversational
- Validate all inputs (email format, phone format, future dates, valid times)
- If information is missing or invalid, ask for it again politely
- Keep track of what information you still need
- Only accept confirmation when ALL required fields are collected
- Available time slots: 09:00, 10:00, 11:00, 12:00, 13:00, 14:00, 15:00, 16:00, 17:00
- Dates must be tomorrow ({(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}) or later, within 6 months from today
- When validating dates, remember that today is {current_date}

RESPONSE FORMAT:
Always respond with a JSON object containing:
{{
  "message": "Your conversational response to the user",
  "state": "current conversation state",
  "data": {{"field": "extracted value"}},
  "needs": ["list of still needed fields"],
  "ready_for_confirmation": true/false
}}

STATES: greeting, collecting, confirming, confirmed"""
    
    def process_message(self, message, current_state, appointment_data):
        """Process user message using AI and return appropriate response"""
        try:
            # Prepare context for the AI
            missing_fields = []
            for field in ['name', 'email', 'phone', 'service', 'date', 'time']:
                if not appointment_data.get(field):
                    missing_fields.append(field)
            
            context = f"""
CURRENT STATE: {current_state}
CURRENT APPOINTMENT DATA: {json.dumps(appointment_data)}
MISSING FIELDS: {missing_fields}
USER MESSAGE: {message}

IMPORTANT: Look carefully at the CURRENT APPOINTMENT DATA to see what information has already been collected. DO NOT ask for information that is already present in the appointment data.

Based on the user's message and current appointment data, determine what to do next and respond appropriately.

If the user mentions a service type (like consultation, medical check-up, dental cleaning, etc.), make sure to extract it and include it in your response data.

Remember to validate any new information and guide the user through the booking process by asking for the NEXT missing field only.
"""

            # Combine system prompt with user context for Gemini
            full_prompt = f"{self.system_prompt}\n\n{context}"
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            if response.text:
                try:
                    ai_response = json.loads(response.text)
                    
                    # Validate and clean the response
                    validated_response = self.validate_ai_response(ai_response, appointment_data)
                    validated_response['source'] = 'ai'  # Mark as AI response
                    return validated_response
                    
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    return self.create_fallback_response(message, current_state, appointment_data)
            else:
                return self.create_fallback_response(message, current_state, appointment_data)
                
        except Exception as e:
            print(f"AI Error: {str(e)}")
            return self.create_fallback_response(message, current_state, appointment_data)
    
    def validate_ai_response(self, ai_response, current_data):
        """Validate and enhance AI response"""
        # Ensure required fields exist
        if 'message' not in ai_response:
            ai_response['message'] = "I'm here to help you book an appointment. Could you please tell me what you need?"
        
        if 'state' not in ai_response:
            ai_response['state'] = 'collecting'
            
        if 'data' not in ai_response:
            ai_response['data'] = {}
            
        # Validate extracted data
        validated_data = {}
        for key, value in ai_response['data'].items():
            if key == 'email' and value:
                if self.validate_email(str(value)):
                    validated_data[key] = str(value).lower()
            elif key == 'phone' and value:
                cleaned_phone = self.clean_phone(str(value))
                if cleaned_phone:
                    validated_data[key] = cleaned_phone
            elif key == 'date' and value:
                parsed_date = self.validate_date(str(value))
                if parsed_date:
                    validated_data[key] = parsed_date
            elif key == 'time' and value:
                parsed_time = self.validate_time(str(value))
                if parsed_time:
                    validated_data[key] = parsed_time
            elif key == 'service' and value:
                # Validate service - accept any of the predefined services or custom service
                service_value = str(value).strip()
                if service_value:
                    # Check if it matches any predefined service (case insensitive)
                    for predefined_service in self.services:
                        if predefined_service.lower() in service_value.lower() or service_value.lower() in predefined_service.lower():
                            validated_data[key] = predefined_service
                            break
                    else:
                        # If no match found, use the custom service
                        validated_data[key] = service_value.title()
            elif key in ['name', 'notes'] and value:
                validated_data[key] = str(value).strip()
        
        ai_response['data'] = validated_data
        
        # Determine what fields are still needed
        all_required = ['name', 'email', 'phone', 'service', 'date', 'time']
        current_data.update(validated_data)
        needs = [field for field in all_required if not current_data.get(field)]
        ai_response['needs'] = needs
        ai_response['ready_for_confirmation'] = len(needs) == 0
        
        return ai_response
    
    def create_fallback_response(self, message, current_state, appointment_data):
        """Create fallback response when AI fails"""
        # Check what information we still need
        required_fields = ['name', 'email', 'phone', 'service', 'date', 'time']
        missing_fields = [field for field in required_fields if not appointment_data.get(field)]
        
        if missing_fields:
            field_name = missing_fields[0].replace('_', ' ')
            return {
                'message': f"I need to collect some more information. Could you please provide your {field_name}?",
                'state': 'collecting',
                'data': {},
                'needs': missing_fields,
                'ready_for_confirmation': False,
                'source': 'fallback'  # Mark as fallback response
            }
        else:
            return {
                'message': "Perfect! I have all your information. Would you like me to book this appointment for you?",
                'state': 'confirming',
                'data': {},
                'needs': [],
                'ready_for_confirmation': True,
                'source': 'fallback'  # Mark as fallback response
            }
    
    def validate_email(self, email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def clean_phone(self, phone):
        """Clean and validate phone number"""
        cleaned = re.sub(r'[\s\-\(\)]', '', phone)
        if cleaned.isdigit() and 10 <= len(cleaned) <= 15:
            return cleaned
        return None
    
    def validate_date(self, date_str):
        """Validate and parse date"""
        formats = ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%B %d, %Y', '%b %d, %Y']
        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_str, fmt).date()
                today = datetime.now().date()
                if date_obj > today and date_obj <= today + timedelta(days=180):
                    return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        return None
    
    def validate_time(self, time_str):
        """Validate and parse time"""
        time_str = time_str.strip().upper().replace('.', ':')
        
        # Handle 12-hour format
        if 'AM' in time_str or 'PM' in time_str:
            try:
                time_obj = datetime.strptime(time_str, '%I:%M %p')
                hour = time_obj.hour
                if 9 <= hour <= 17:
                    return f"{hour:02d}:00"
            except ValueError:
                pass
        
        # Handle 24-hour format
        patterns = [r'^(\d{1,2}):(\d{2})$', r'^(\d{1,2})$']
        for pattern in patterns:
            match = re.match(pattern, time_str)
            if match:
                hour = int(match.group(1))
                if 9 <= hour <= 17:
                    return f"{hour:02d}:00"
        
        return None
