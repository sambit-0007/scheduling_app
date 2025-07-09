# Scheduling Chatbot

This project implements a simple WhatsApp scheduling assistant using Flask,
Twilio and an OpenAI-compatible API (e.g. Grok API).

## Features
- Receive WhatsApp messages via Twilio webhook.
- Use an LLM to understand booking requests and FAQs.
- Store appointments in a local SQLite database.
- Basic FAQ handling for shop hours, services and location.

## Setup
1. Create a virtual environment and install requirements:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Create a `.env` file based on `.env.example` and fill in your keys:
   - `OPENAI_API_KEY` – API key for Grok/OpenAI.
   - `TWILIO_AUTH_TOKEN` – used to verify Twilio requests (optional).
   - `DATABASE_PATH` – path to SQLite DB (default `appointments.db`).
3. Run the application:
   ```bash
   flask run
   ```
   The app listens on `/webhook` for POST requests from Twilio.

## Deployment
You can deploy this on platforms such as Replit or Render. Ensure you set the
above environment variables in the service's dashboard and expose the `/webhook`
endpoint to Twilio.

## Notes
- For production, secure the webhook using Twilio request validation.
- The LLM prompt expects JSON output; adjust as needed for your model.
- You can expand `check_availability` to integrate with Google Calendar.
