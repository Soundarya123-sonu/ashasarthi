import os
import html
import hashlib
import secrets
import smtplib
import logging

from datetime import date
from urllib.parse import urlencode
from email.message import EmailMessage

import mysql.connector
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AshaSarthi Email Confirmation API")

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
PUBLIC_API_URL = os.getenv(
    "PUBLIC_API_URL", "http://127.0.0.1:8000"
).rstrip("/")


def get_db():
    required = ("MYSQLHOST", "MYSQLUSER", "MYSQLPASSWORD", "MYSQLDATABASE")
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise RuntimeError(
            "Missing MySQL environment variables: " + ", ".join(missing)
        )

    return mysql.connector.connect(
        host=os.getenv("MYSQLHOST"),
        port=int(os.getenv("MYSQLPORT", "3306")),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE"),
        connection_timeout=10,
    )


def initialize_database():
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_confirmations (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                beneficiary_name VARCHAR(150) NOT NULL,
                beneficiary_email VARCHAR(254) NOT NULL,
                next_visit_date DATE NOT NULL,
                token_hash CHAR(64) NOT NULL UNIQUE,
                response ENUM('yes', 'no') NULL DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                responded_at TIMESTAMP NULL DEFAULT NULL
            )
        """)
        conn.commit()
        cursor.close()
    finally:
        conn.close()


@app.on_event("startup")
def startup():
    initialize_database()


class VisitEmailRequest(BaseModel):
    beneficiary_name: str
    beneficiary_email: EmailStr
    next_visit_date: date


def send_visit_email(name, recipient, visit_date, token):
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        raise RuntimeError(
            "Gmail SMTP configuration is missing. Set SMTP_EMAIL and SMTP_PASSWORD in .env."
        )

    query_yes = urlencode({"token": token, "choice": "yes"})
    query_no = urlencode({"token": token, "choice": "no"})
    yes_url = f"{PUBLIC_API_URL}/respond?{query_yes}"
    no_url = f"{PUBLIC_API_URL}/respond?{query_no}"
    safe_name = html.escape(name)

    msg = EmailMessage()
    msg["Subject"] = "AshaSarthi - Visit Confirmation"
    msg["From"] = SMTP_EMAIL
    msg["To"] = recipient
    msg.set_content(
        f"Hello {name},\\n"
        f"Your next visit is scheduled for {visit_date}.\\n"
        f"Available: {yes_url}\\n"
        f"Not available: {no_url}\\n"
    )
    msg.add_alternative(f"""
    <html><body style="font-family:Arial">
      <h2>AshaSarthi - Visit Confirmation</h2>
      <p>Hello {safe_name},</p>
      <p>Your next visit is scheduled for <b>{html.escape(visit_date)}</b>.</p>
      <p>Will you be available?</p>
      <a href="{html.escape(yes_url, quote=True)}"
         style="background:#16803d;color:white;padding:12px;text-decoration:none">
         Yes, Available</a>
      &nbsp;
      <a href="{html.escape(no_url, quote=True)}"
         style="background:#b42318;color:white;padding:12px;text-decoration:none">
         No, Not Available</a>
    </body></html>
    """, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
        server.login(SMTP_EMAIL, SMTP_PASSWORD.replace(" ", ""))
        server.send_message(msg)


@app.post("/send-visit-email")
def send_visit_email_api(data: VisitEmailRequest):
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO email_confirmations
            (beneficiary_name, beneficiary_email, next_visit_date, token_hash)
            VALUES (%s, %s, %s, %s)
        """, (
            data.beneficiary_name,
            str(data.beneficiary_email),
            data.next_visit_date,
            token_hash,
        ))
        conn.commit()
        confirmation_id = cursor.lastrowid
        cursor.close()
    finally:
        conn.close()

    try:
        send_visit_email(
            data.beneficiary_name,
            str(data.beneficiary_email),
            data.next_visit_date.isoformat(),
            token,
        )
    except Exception as exc:
        logger.exception("Email sending failed")
        conn = get_db()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM email_confirmations WHERE id = %s",
                (confirmation_id,),
            )
            conn.commit()
            cursor.close()
        finally:
            conn.close()

        raise HTTPException(
            status_code=502,
            detail=f"Email sending failed ({type(exc).__name__}). Check backend terminal logs and .env settings.",
        ) from exc

    return {"message": "Confirmation email sent successfully"}


@app.get("/respond", response_class=HTMLResponse)
def show_response_form(token: str, choice: str):
    if choice not in ("yes", "no"):
        raise HTTPException(status_code=400, detail="Invalid choice")

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT response, created_at
            FROM email_confirmations
            WHERE token_hash = %s
              AND created_at >= NOW() - INTERVAL 7 DAY
        """, (token_hash,))
        record = cursor.fetchone()
        cursor.close()
    finally:
        conn.close()

    if not record:
        raise HTTPException(status_code=404, detail="Link is invalid or expired")

    if record["response"] is not None:
        return HTMLResponse("<h3>Your response has already been recorded.</h3>")

    label = "Yes, I am available" if choice == "yes" else "No, I am not available"
    safe_token = html.escape(token, quote=True)
    return HTMLResponse(f"""
    <html><body style="font-family:Arial;padding:30px">
      <h2>AshaSarthi Visit Confirmation</h2>
      <p>Please confirm your response:</p>
      <form method="post" action="/respond">
        <input type="hidden" name="token" value="{safe_token}">
        <input type="hidden" name="choice" value="{choice}">
        <button type="submit" style="padding:12px 20px;cursor:pointer">
          Confirm: {label}
        </button>
      </form>
    </body></html>
    """)


@app.post("/respond", response_class=HTMLResponse)
def save_response(token: str = Form(...), choice: str = Form(...)):
    if choice not in ("yes", "no"):
        raise HTTPException(status_code=400, detail="Invalid choice")

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE email_confirmations
            SET response = %s, responded_at = NOW()
            WHERE token_hash = %s
              AND response IS NULL
              AND created_at >= NOW() - INTERVAL 7 DAY
        """, (choice, token_hash))
        updated = cursor.rowcount
        conn.commit()
        cursor.close()
    finally:
        conn.close()

    if updated == 0:
        raise HTTPException(
            status_code=400,
            detail="Response already recorded or link expired",
        )

    return HTMLResponse("<h2>Thank you!</h2><p>Your response has been saved successfully.</p>")


@app.get("/visit-responses")
def get_visit_responses():
    # Add authentication/authorization before production use.
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, beneficiary_name, beneficiary_email,
                   next_visit_date, response, created_at, responded_at
            FROM email_confirmations
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        return rows
    finally:
        conn.close()


@app.get("/")
def home():
    return {"message": "AshaSarthi Email API is running"}
