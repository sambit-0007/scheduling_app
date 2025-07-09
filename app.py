import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
import openai
import sqlite3
import logging

load_dotenv()

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")
DATABASE = os.getenv("DATABASE_PATH", "appointments.db")

logging.basicConfig(level=logging.INFO)


def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT,
            name TEXT,
            service TEXT,
            date TEXT,
            time TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def parse_message(message: str) -> dict:
    prompt = f"""
    Extract intent and entities from the user's message.
    Return JSON with fields: intent (book, cancel, info), service, date, time, name.
    Message: \"{message}\"
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        content = response.choices[0].message["content"]
        import json

        data = json.loads(content)
        return data
    except Exception:
        logging.exception("LLM parsing error")
        return {}


def check_availability(date: str, time: str) -> bool:
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT 1 FROM appointments WHERE date=? AND time=?", (date, time))
    available = c.fetchone() is None
    conn.close()
    return available


def save_appointment(phone: str, name: str, service: str, date: str, time: str) -> None:
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO appointments (phone, name, service, date, time) VALUES (?, ?, ?, ?, ?)",
        (phone, name, service, date, time),
    )
    conn.commit()
    conn.close()


FAQ_RESPONSES = {
    "hours": "We are open Tuesday to Saturday 9AM - 6PM.",
    "services": "We offer haircuts, coloring, and styling.",
    "location": "We are located at 123 Main St.",
}


@app.route("/webhook", methods=["POST"])
def webhook():
    init_db()
    from_number = request.form.get("From")
    body = request.form.get("Body", "")
    logging.info("Incoming message from %s: %s", from_number, body)

    resp = MessagingResponse()

    lower_body = body.lower().strip()
    if lower_body in FAQ_RESPONSES:
        resp.message(FAQ_RESPONSES[lower_body])
        return str(resp)

    parsed = parse_message(body)
    intent = parsed.get("intent")

    if intent == "book":
        service = parsed.get("service")
        date = parsed.get("date")
        time_str = parsed.get("time")
        name = parsed.get("name", from_number)

        if not all([service, date, time_str]):
            resp.message(
                "Sorry, I couldn't understand your request. Please provide service, date, and time."
            )
            return str(resp)

        if check_availability(date, time_str):
            save_appointment(from_number, name, service, date, time_str)
            resp.message(f"Confirmed {service} on {date} at {time_str} for {name}.")
        else:
            resp.message(
                "Sorry, that slot is not available. Please choose another time."
            )
    elif intent == "cancel":
        resp.message("To cancel, please contact the shop directly.")
    elif intent == "info":
        resp.message("You can ask about our hours, services, or location.")
    else:
        resp.message(
            "Sorry, I didn't understand that. Please try again or contact the shop."
        )

    return str(resp)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
