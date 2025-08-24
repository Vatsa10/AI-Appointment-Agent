# AI Appointment Agent

An intelligent chatbot that helps users book, reschedule, and manage appointments through a conversational interface. The application integrates with Google Sheets for data storage and sends email confirmations for appointments.

## Features

- **Conversational Interface**: Natural language processing for intuitive appointment booking
- **Google Sheets Integration**: Secure storage of all appointment data
- **Email Notifications**: Automated confirmation emails for appointments
- **Responsive Design**: Works on both desktop and mobile devices
- **Session Management**: Maintains conversation context during interactions

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Google Cloud Platform account with Google Sheets API enabled
- Gmail account for sending emails (or any SMTP-compatible email service)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Vatsa10/AI-Appointment-Agent.git
   cd AI-Appointment-Agent
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Update the values in `.env` with your configuration:
     ```
     SESSION_SECRET=your_session_secret
     BUSINESS_EMAIL=your_business_email@example.com
     BUSINESS_NAME="Your Business Name"
     EMAIL_ADDRESS=your_email@example.com
     EMAIL_PASSWORD=your_email_app_password
     GOOGLE_SHEETS_CREDENTIALS=path/to/your/credentials.json
     GOOGLE_SPREADSHEET_ID=your_google_sheet_id
     ```

## Usage

1. Run the application:
   ```bash
   streamlit run app.py
   ```

2. Open your browser and navigate to `http://localhost:8501`

3. Start chatting with the AI assistant to book or manage appointments

## Project Structure

- `app.py`: Main application file with Streamlit UI
- `chatbot_handler.py`: Handles conversation logic and state management
- `email_handler.py`: Manages email notifications
- `google_sheets_handler.py`: Handles interactions with Google Sheets
- `.env.example`: Template for environment variables

## How It Works

1. The chatbot greets the user and asks for appointment details
2. It collects necessary information (date, time, service type, contact details)
3. The appointment is saved to Google Sheets
4. A confirmation email is sent to the user
5. The user can reschedule or cancel through the chat interface

## Security

- All sensitive data is stored in environment variables
- Google Sheets API uses OAuth 2.0 for secure authentication
- Email credentials are never stored in the codebase

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Uses Google Sheets API for data storage
- Email notifications powered by Python's smtplib
