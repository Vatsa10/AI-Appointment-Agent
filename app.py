import streamlit as st
import os
from datetime import datetime, timedelta
from google_sheets_handler import GoogleSheetsHandler
from email_handler import EmailHandler
from chatbot_handler import ChatbotHandler

# Load environment variables from .env file for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, using environment variables directly

# Page configuration
st.set_page_config(
    page_title="Appointment Booking Chatbot",
    page_icon="📅",
    layout="wide"
)

def initialize_session_state():
    """Initialize session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'conversation_state' not in st.session_state:
        st.session_state.conversation_state = 'greeting'
    if 'appointment_data' not in st.session_state:
        st.session_state.appointment_data = {}
    if 'sheets_handler' not in st.session_state:
        st.session_state.sheets_handler = GoogleSheetsHandler()
    if 'email_handler' not in st.session_state:
        st.session_state.email_handler = EmailHandler()
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = ChatbotHandler()

def main():
    """Main application function"""
    st.title("📅 Appointment Booking Assistant")
    st.write("Welcome! I'm here to help you book an appointment. Let's get started!")
    
    # Initialize session state
    initialize_session_state()
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Handle user input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process user input and get bot response
        try:
            bot_response = st.session_state.chatbot.process_message(
                prompt, 
                st.session_state.conversation_state,
                st.session_state.appointment_data
            )
            
            # Update conversation state and appointment data
            st.session_state.conversation_state = bot_response.get('state', st.session_state.conversation_state)
            st.session_state.appointment_data.update(bot_response.get('data', {}))
            
            # Add bot response to chat history
            st.session_state.messages.append({"role": "assistant", "content": bot_response['message']})
            with st.chat_message("assistant"):
                st.markdown(bot_response['message'])
            
            # Handle appointment confirmation
            if (st.session_state.conversation_state == 'confirmed' or 
                (bot_response.get('ready_for_confirmation') and 
                 any(word in prompt.lower() for word in ['yes', 'confirm', 'book', 'ok']))):
                try:
                    # Save to Google Sheets
                    sheets_result = st.session_state.sheets_handler.add_appointment(
                        st.session_state.appointment_data
                    )
                    
                    if sheets_result['success']:
                        # Send email notifications
                        email_result = st.session_state.email_handler.send_notifications(
                            st.session_state.appointment_data
                        )
                        
                        if email_result['success']:
                            success_msg = "✅ Perfect! Your appointment has been booked successfully. You'll receive a confirmation email shortly."
                        else:
                            success_msg = f"✅ Your appointment has been booked successfully, but there was an issue sending the email: {email_result['error']}"
                        
                        st.session_state.messages.append({"role": "assistant", "content": success_msg})
                        with st.chat_message("assistant"):
                            st.markdown(success_msg)
                        
                        # Reset for new booking
                        st.session_state.conversation_state = 'greeting'
                        st.session_state.appointment_data = {}
                    else:
                        error_msg = f"❌ Sorry, there was an error saving your appointment: {sheets_result['error']}. Please try again."
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                        with st.chat_message("assistant"):
                            st.markdown(error_msg)
                        
                except Exception as e:
                    error_msg = f"❌ An unexpected error occurred: {str(e)}. Please try again."
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    with st.chat_message("assistant"):
                        st.markdown(error_msg)
                
                st.rerun()
        
        except Exception as e:
            error_msg = f"❌ Sorry, I encountered an error processing your message: {str(e)}. Please try again."
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            with st.chat_message("assistant"):
                st.markdown(error_msg)
    
    # Sidebar with current appointment details
    with st.sidebar:
        st.header("Current Booking Details")
        if st.session_state.appointment_data:
            for key, value in st.session_state.appointment_data.items():
                if value:
                    st.write(f"**{key.replace('_', ' ').title()}:** {value}")
        else:
            st.write("No booking details yet.")
        
        # Reset conversation button
        if st.button("Start New Booking"):
            st.session_state.messages = []
            st.session_state.conversation_state = 'greeting'
            st.session_state.appointment_data = {}
            st.rerun()

if __name__ == "__main__":
    main()
