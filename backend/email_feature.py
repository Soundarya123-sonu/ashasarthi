import os
import secrets
import smtplib
from datetime import date, datetime, timezone
from email.message import EmailMessage
from threading import Lock
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

router = APIRouter(tags=["Email Visit Confirmation"])

# Prototype-only storage. Replace with database persistence before production.
_invites = {}
_lock = Lock()


class SendVisitEmailRequest(BaseModel):
    beneficiary_name: str = Field(min_length=1, max_length=191)
    beneficiary_email: EmailStr
    worker_name: str = Field(min_length=1, max_length=191)
    message: str = Field(default="Please confirm your upcoming visit.", max_length=2000)
    proposed_visit_date: Optional[date] = None


class VisitResponseRequest(BaseModel):
    answer: str
    next_visit_date: Optional[date] = None


def _send_email(to_email: str, subject: str, body: str) -> None:
    host = os.getenv("SMTP_HOST")
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("SMTP_FROM_EMAIL") or username
    port = int(os.getenv("SMTP_PORT", "587"))

    if not all([host, username, password, from_email]):
        raise HTTPException(
            status_code=503,
            detail="Email is not configured. Set SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD and SMTP_FROM_EMAIL.",
        )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_email
    message["To"] = to_email
    message.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        raise HTTPException(status_code=502, detail="Unable to send email. Check SMTP settings.") from exc


@router.post("/email-visits/send")
def send_visit_email(data: SendVisitEmailRequest):
    token = secrets.token_urlsafe(24)
    api_base = os.getenv("API_PUBLIC_BASE_URL", "").rstrip("/")
    if not api_base:
        raise HTTPException(
            status_code=503,
            detail="Set API_PUBLIC_BASE_URL to the publicly reachable API base URL.",
        )

    response_url = f"{api_base}/email-visits/{token}"
    proposed = f"\nProposed visit date: {data.proposed_visit_date.isoformat()}" if data.proposed_visit_date else ""
    body = (
        f"Hello {data.beneficiary_name},\n\n"
        f"{data.worker_name} has sent you a visit confirmation request.\n\n"
        f"{data.message}{proposed}\n\n"
        f"Please open this link to respond YES or NO and optionally provide your next visit date:\n"
        f"{response_url}\n\n"
        "If you were not expecting this email, you can ignore it."
    )

    _send_email(
        data.beneficiary_email,
        "Asha Sarthi — Visit Confirmation",
        body,
    )

    with _lock:
        _invites[token] = {
            "beneficiary_name": data.beneficiary_name,
            "beneficiary_email": str(data.beneficiary_email),
            "worker_name": data.worker_name,
            "message": data.message,
            "proposed_visit_date": data.proposed_visit_date.isoformat() if data.proposed_visit_date else None,
            "answer": None,
            "next_visit_date": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    return {"success": True, "message": "Visit confirmation email sent.", "token": token}


@router.get("/email-visits/{token}")
def get_visit_invite(token: str):
    with _lock:
        invite = _invites.get(token)
        if not invite:
            raise HTTPException(status_code=404, detail="Invitation not found or expired.")
        return {"success": True, "invitation": invite}


@router.post("/email-visits/{token}/respond")
def respond_to_visit(token: str, data: VisitResponseRequest):
    answer = data.answer.strip().upper()
    if answer not in {"YES", "NO"}:
        raise HTTPException(status_code=400, detail="Answer must be YES or NO.")

    with _lock:
        invite = _invites.get(token)
        if not invite:
            raise HTTPException(status_code=404, detail="Invitation not found or expired.")
        invite["answer"] = answer
        invite["next_visit_date"] = data.next_visit_date.isoformat() if data.next_visit_date else None
        invite["responded_at"] = datetime.now(timezone.utc).isoformat()

    return {
        "success": True,
        "message": "Response saved.",
        "answer": answer,
        "next_visit_date": invite["next_visit_date"],
    }
