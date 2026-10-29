import os
import json
import hashlib
import hmac
import base64
import secrets
import logging
from datetime import date, datetime, timezone, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from html import escape

import mysql.connector
from dotenv import load_dotenv
<<<<<<< HEAD
from fastapi import FastAPI, HTTPException, Form, Header
from fastapi.middleware.cors import CORSMiddleware
=======
from fastapi import FastAPI, HTTPException, Form, Header, Depends
>>>>>>> 0575884 (Switch email service to Gmail SMTP)
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr, Field

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ashasarthi")

<<<<<<< HEAD
app = FastAPI(title="AshaSarthi Cloud Sync and Email API", version="1.1.0")

# CORS: broad settings are useful for initial testing.
# For production, replace "*" with your actual frontend origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_ENTITIES = {"beneficiary", "child", "pregnancy", "visit"}
PUBLIC_API_URL = os.getenv(
    "PUBLIC_API_URL", "https://ashasarthi.onrender.com"
).rstrip("/")
=======
app = FastAPI(title="AshaSarthi Cloud Sync, Auth and Email API", version="2.0.0")
ALLOWED_ENTITIES = {"beneficiary", "child", "pregnancy", "visit"}
PUBLIC_API_URL = os.getenv("PUBLIC_API_URL", "http://127.0.0.1:8000").rstrip("/")
TOKEN_HOURS = 24
>>>>>>> 0575884 (Switch email service to Gmail SMTP)


def get_db_connection():
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
        connection_timeout=15,
        autocommit=False,
    )


def initialize_database():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
<<<<<<< HEAD
        cursor.execute(
            """
=======
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_users (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(150) NOT NULL,
                role VARCHAR(40) NOT NULL DEFAULT 'asha',
                email VARCHAR(254) NOT NULL UNIQUE,
                mobile VARCHAR(30) NULL,
                village VARCHAR(150) NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
>>>>>>> 0575884 (Switch email service to Gmail SMTP)
            CREATE TABLE IF NOT EXISTS cloud_sync_records (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT NULL,
                entity VARCHAR(40) NOT NULL,
                record_key VARCHAR(191) NOT NULL,
                payload JSON NOT NULL,
                deleted BOOLEAN NOT NULL DEFAULT FALSE,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_sync_user_updated (user_id, updated_at)
            )
<<<<<<< HEAD
            """
        )
        cursor.execute(
            """
=======
        """)
        # Safe migration from the previous table schema.
        cursor.execute("SHOW COLUMNS FROM cloud_sync_records LIKE 'user_id'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE cloud_sync_records ADD COLUMN user_id BIGINT NULL")
        cursor.execute("SHOW INDEX FROM cloud_sync_records WHERE Key_name = 'uq_entity_record'")
        if cursor.fetchone():
            cursor.execute("ALTER TABLE cloud_sync_records DROP INDEX uq_entity_record")
        cursor.execute("SHOW INDEX FROM cloud_sync_records WHERE Key_name = 'uq_user_entity_record'")
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE cloud_sync_records
                ADD UNIQUE KEY uq_user_entity_record (user_id, entity, record_key)
            """)
        cursor.execute("""
>>>>>>> 0575884 (Switch email service to Gmail SMTP)
            CREATE TABLE IF NOT EXISTS email_confirmations (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                beneficiary_name VARCHAR(150) NOT NULL,
                beneficiary_email VARCHAR(254) NOT NULL,
                next_visit_date DATE NOT NULL,
                token_hash CHAR(64) NOT NULL UNIQUE,
                response ENUM('yes', 'no') NULL DEFAULT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                responded_at TIMESTAMP NULL DEFAULT NULL,
                INDEX idx_confirmation_created (created_at)
            )
            """
        )
        conn.commit()
        cursor.close()
        logger.info("AshaSarthi database tables are ready.")
    finally:
        conn.close()


@app.on_event("startup")
def startup():
    try:
        initialize_database()
    except Exception:
        # Keep the service available so health endpoints explain database issues.
        logger.exception("Database initialization failed during startup")


@app.get("/")
def home():
    return {
        "message": "AshaSarthi API is running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "ashasarthi"}


@app.get("/health/db")
def database_health():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        return {
            "status": "ok",
            "database": "connected",
            "test_result": result[0],
        }
    except Exception as exc:
        logger.exception("Database health check failed")
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {type(exc).__name__}",
        ) from None
    finally:
        if conn is not None and conn.is_connected():
            conn.close()


<<<<<<< HEAD
# -------------------- Cloud sync endpoints --------------------

=======
# ---------------- Authentication ----------------
class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    role: str = Field(default="asha", min_length=2, max_length=40)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    village: str | None = Field(default=None, max_length=150)
    mobile: str | None = Field(default=None, max_length=30)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str | None = None


def _password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310000)
    return base64.b64encode(salt).decode() + "$" + base64.b64encode(digest).decode()


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt_text, digest_text = stored.split("$", 1)
        salt = base64.b64decode(salt_text)
        expected = base64.b64decode(digest_text)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310000)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _create_token(user_id: int) -> str:
    secret = os.getenv("AUTH_SECRET", "")
    if len(secret) < 32:
        raise HTTPException(status_code=500, detail="Set a random AUTH_SECRET of at least 32 characters in Render.")
    expires = int((datetime.now(timezone.utc) + timedelta(hours=TOKEN_HOURS)).timestamp())
    payload = f"{user_id}:{expires}"
    signature = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}:{signature}".encode()).decode().rstrip("=")


def get_current_user(authorization: str | None = Header(default=None)):
    secret = os.getenv("AUTH_SECRET", "")
    if len(secret) < 32:
        raise HTTPException(status_code=500, detail="Authentication is not configured.")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Login required.")
    try:
        token = authorization[7:].strip()
        decoded = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4)).decode()
        uid_text, expiry_text, signature = decoded.split(":", 2)
        payload = f"{uid_text}:{expiry_text}"
        expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError("Bad signature")
        user_id, expiry = int(uid_text), int(expiry_text)
        if expiry < int(datetime.now(timezone.utc).timestamp()):
            raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
        return {"user_id": user_id}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid login token.") from None


def _public_user(row):
    return {
        "id": row["id"], "name": row["name"], "role": row["role"],
        "email": row["email"], "mobile": row.get("mobile"),
        "village": row.get("village"),
    }


@app.post("/register")
def register(data: RegisterRequest):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        email = str(data.email).strip().lower()
        cursor.execute("SELECT id FROM app_users WHERE email=%s", (email,))
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="Email already registered.")
        cursor.execute("""
            INSERT INTO app_users (name, role, email, mobile, village, password_hash)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data.name.strip(), data.role.strip().lower(), email,
            data.mobile, data.village, _password_hash(data.password)
        ))
        user_id = cursor.lastrowid
        conn.commit()
        user = {
            "id": user_id, "name": data.name.strip(), "role": data.role.strip().lower(),
            "email": email, "mobile": data.mobile, "village": data.village,
        }
        cursor.close()
        return {"success": True, "data": user, "user": user,
                "access_token": _create_token(user_id), "token_type": "bearer"}
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except mysql.connector.IntegrityError:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=409, detail="Email already registered.") from None
    except Exception:
        if conn:
            conn.rollback()
        logger.exception("Registration failed")
        raise HTTPException(status_code=503, detail="Registration failed. Check database configuration.") from None
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.post("/login")
def login(data: LoginRequest):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM app_users WHERE email=%s", (str(data.email).strip().lower(),))
        row = cursor.fetchone()
        cursor.close()
        if not row or not _verify_password(data.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        if data.role and row["role"].lower() != data.role.strip().lower():
            raise HTTPException(status_code=401, detail="This account does not match the selected role.")
        user = _public_user(row)
        return {"success": True, "data": user, "user": user,
                "access_token": _create_token(row["id"]), "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Login failed")
        raise HTTPException(status_code=503, detail="Login service unavailable.") from None
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM app_users WHERE id=%s", (current_user["user_id"],))
        row = cursor.fetchone()
        cursor.close()
        if not row:
            raise HTTPException(status_code=401, detail="User not found.")
        return {"success": True, "user": _public_user(row)}
    finally:
        if conn and conn.is_connected():
            conn.close()


# ---------------- User-isolated cloud sync ----------------
>>>>>>> 0575884 (Switch email service to Gmail SMTP)
class SyncRecord(BaseModel):
    entity: str
    record_id: str = Field(min_length=1, max_length=191)
    payload: dict = Field(default_factory=dict)
    deleted: bool = False


class SyncPushRequest(BaseModel):
    records: list[SyncRecord] = Field(default_factory=list, max_length=500)


def validate_entity(entity: str):
    if entity not in ALLOWED_ENTITIES:
        allowed = ", ".join(sorted(ALLOWED_ENTITIES))
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported entity. Allowed: {allowed}",
        )


def upsert_sync_record(cursor, user_id: int, record: SyncRecord):
    validate_entity(record.entity)
<<<<<<< HEAD
    cursor.execute(
        """
        INSERT INTO cloud_sync_records (entity, record_key, payload, deleted)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            payload = VALUES(payload),
            deleted = VALUES(deleted),
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            record.entity,
            record.record_id,
            json.dumps(record.payload, ensure_ascii=False),
            record.deleted,
        ),
    )
=======
    cursor.execute("""
        INSERT INTO cloud_sync_records (user_id, entity, record_key, payload, deleted)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            payload=VALUES(payload), deleted=VALUES(deleted),
            updated_at=CURRENT_TIMESTAMP
    """, (user_id, record.entity, record.record_id,
          json.dumps(record.payload, ensure_ascii=False), record.deleted))
>>>>>>> 0575884 (Switch email service to Gmail SMTP)


@app.post("/sync/push")
def sync_push(data: SyncPushRequest, current_user: dict = Depends(get_current_user)):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        for record in data.records:
            upsert_sync_record(cursor, current_user["user_id"], record)
        conn.commit()
        cursor.close()
        return {"success": True, "count": len(data.records)}
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception:
        if conn:
            conn.rollback()
        logger.exception("Sync push failed")
<<<<<<< HEAD
        raise HTTPException(
            status_code=503,
            detail=f"Could not save cloud records ({type(exc).__name__})",
        ) from None
=======
        raise HTTPException(status_code=503, detail="Could not save cloud records.") from None
>>>>>>> 0575884 (Switch email service to Gmail SMTP)
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.get("/sync/pull")
def sync_pull(entity: str | None = None, include_deleted: bool = True,
              limit: int = 500, current_user: dict = Depends(get_current_user)):
    if entity is not None:
        validate_entity(entity)
    limit = max(1, min(limit, 1000))
    conn = None
    try:
<<<<<<< HEAD
        if entity is not None:
            validate_entity(entity)

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = (
            "SELECT entity, record_key, payload, deleted, updated_at "
            "FROM cloud_sync_records"
        )
        conditions = []
        params = []

=======
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """SELECT entity, record_key, payload, deleted, updated_at
                   FROM cloud_sync_records WHERE user_id=%s"""
        params = [current_user["user_id"]]
>>>>>>> 0575884 (Switch email service to Gmail SMTP)
        if entity is not None:
            query += " AND entity=%s"
            params.append(entity)
        if not include_deleted:
<<<<<<< HEAD
            conditions.append("deleted = FALSE")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY updated_at ASC"

=======
            query += " AND deleted=FALSE"
        query += " ORDER BY updated_at ASC LIMIT %s"
        params.append(limit)
>>>>>>> 0575884 (Switch email service to Gmail SMTP)
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        records = []

        for row in rows:
            payload = row["payload"]
            if isinstance(payload, (bytes, bytearray)):
                payload = payload.decode("utf-8")
            if isinstance(payload, str):
                payload = json.loads(payload)
<<<<<<< HEAD

            records.append(
                {
                    "entity": row["entity"],
                    "record_id": row["record_key"],
                    "payload": payload,
                    "deleted": bool(row["deleted"]),
                    "updated_at": (
                        row["updated_at"].isoformat()
                        if row["updated_at"]
                        else None
                    ),
                }
            )

=======
            records.append({
                "entity": row["entity"], "record_id": row["record_key"],
                "payload": payload, "deleted": bool(row["deleted"]),
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
            })
>>>>>>> 0575884 (Switch email service to Gmail SMTP)
        cursor.close()
        return {
            "success": True,
            "count": len(records),
            "records": records,
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Sync pull failed")
<<<<<<< HEAD
        raise HTTPException(
            status_code=503,
            detail=f"Could not read cloud records ({type(exc).__name__})",
        ) from None
=======
        raise HTTPException(status_code=503, detail="Could not read cloud records.") from None
>>>>>>> 0575884 (Switch email service to Gmail SMTP)
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.post("/sync/{entity}")
def sync_entity(entity: str, payload: dict, current_user: dict = Depends(get_current_user)):
    validate_entity(entity)
    record_id = payload.get("record_id", payload.get("id"))
    if record_id is None or str(record_id).strip() == "":
<<<<<<< HEAD
        raise HTTPException(
            status_code=422,
            detail="Payload must contain 'id' or 'record_id'",
        )

    record = SyncRecord(
        entity=entity,
        record_id=str(record_id),
        payload=payload,
        deleted=bool(payload.get("deleted", False)),
    )
=======
        raise HTTPException(status_code=422, detail="Payload must contain 'id' or 'record_id'.")
    record = SyncRecord(entity=entity, record_id=str(record_id),
                        payload=payload, deleted=bool(payload.get("deleted", False)))
>>>>>>> 0575884 (Switch email service to Gmail SMTP)
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        upsert_sync_record(cursor, current_user["user_id"], record)
        conn.commit()
        cursor.close()
<<<<<<< HEAD
        return {
            "success": True,
            "entity": entity,
            "record_id": str(record_id),
        }
    except Exception as exc:
        if conn is not None:
            conn.rollback()
        logger.exception("Entity sync failed")
        raise HTTPException(
            status_code=503,
            detail=f"Could not sync record ({type(exc).__name__})",
        ) from None
=======
        return {"success": True, "entity": entity, "record_id": str(record_id)}
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception:
        if conn:
            conn.rollback()
        logger.exception("Entity sync failed")
        raise HTTPException(status_code=503, detail="Could not sync record.") from None
>>>>>>> 0575884 (Switch email service to Gmail SMTP)
    finally:
        if conn and conn.is_connected():
            conn.close()


<<<<<<< HEAD
# -------------------- Beneficiary visit email --------------------

=======


# Beneficiary email confirmation through Gmail SMTP
>>>>>>> 0575884 (Switch email service to Gmail SMTP)
class VisitEmailRequest(BaseModel):
    beneficiary_name: str = Field(min_length=1, max_length=150)
    beneficiary_email: EmailStr
    next_visit_date: date


def send_email(to_email: str, subject: str, text_body: str, html_body: str):
<<<<<<< HEAD
    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("EMAIL_FROM", "onboarding@resend.dev")

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="RESEND_API_KEY is not configured in Render Environment.",
        )

    body = json.dumps(
        {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "text": text_body,
            "html": html_body,
        }
    ).encode("utf-8")

    request = Request(
        "https://api.resend.com/emails",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "AshaSarthi-API/1.1",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=25) as response:
            result = json.loads(response.read().decode("utf-8"))
            logger.info("Email accepted by Resend. id=%s", result.get("id", "unknown"))
            return result
    except HTTPError as exc:
        provider_error = exc.read().decode("utf-8", errors="replace")[:500]
        logger.error("Resend API error HTTP %s: %s", exc.code, provider_error)
        raise HTTPException(
            status_code=502,
            detail=(
                f"Email provider rejected the request (HTTP {exc.code}). "
                "Check Resend sender verification and recipient restrictions."
            ),
        ) from None
    except (URLError, TimeoutError, OSError):
        logger.exception("Could not connect to Resend")
        raise HTTPException(
            status_code=502,
            detail="Could not connect to the email provider API.",
        ) from None
    except (ValueError, json.JSONDecodeError):
        logger.exception("Unexpected Resend response")
        raise HTTPException(
            status_code=502,
            detail="Unexpected response from the email provider.",
=======
    """Send an email using Gmail SMTP and a Google App Password."""
    smtp_email = os.getenv("SMTP_EMAIL")
    smtp_app_password = os.getenv("SMTP_APP_PASSWORD")

    if not smtp_email or not smtp_app_password:
        raise HTTPException(
            status_code=503,
            detail="SMTP_EMAIL and SMTP_APP_PASSWORD must be configured in the backend environment."
        )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"AshaSarthi <{smtp_email}>"
    message["To"] = to_email
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    try:
        import smtplib
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=25) as smtp:
            smtp.login(smtp_email, smtp_app_password.replace(" ", ""))
            smtp.send_message(message)
        logger.info("Email sent successfully via Gmail SMTP to %s", to_email)
        return {"success": True}
    except Exception as exc:
        logger.exception("Gmail SMTP email sending failed")
        raise HTTPException(
            status_code=502,
            detail=f"Gmail SMTP could not send the email ({type(exc).__name__}). Check SMTP_EMAIL and SMTP_APP_PASSWORD."
>>>>>>> 0575884 (Switch email service to Gmail SMTP)
        ) from None


def create_and_send_visit_email(data: VisitEmailRequest):
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    conn = None
    confirmation_id = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO email_confirmations
                (beneficiary_name, beneficiary_email, next_visit_date, token_hash)
            VALUES (%s, %s, %s, %s)
            """,
            (
                data.beneficiary_name,
                str(data.beneficiary_email),
                data.next_visit_date,
                token_hash,
            ),
        )
        conn.commit()
        confirmation_id = cursor.lastrowid
        cursor.close()
    except Exception as exc:
        if conn is not None:
            conn.rollback()
        logger.exception("Could not create email confirmation")
        raise HTTPException(
            status_code=503,
            detail=f"Could not save email confirmation ({type(exc).__name__})",
        ) from None
    finally:
        if conn is not None and conn.is_connected():
            conn.close()

    yes_url = f"{PUBLIC_API_URL}/respond?{urlencode({'token': token, 'choice': 'yes'})}"
    no_url = f"{PUBLIC_API_URL}/respond?{urlencode({'token': token, 'choice': 'no'})}"
    safe_name = escape(data.beneficiary_name)
    visit_date = data.next_visit_date.isoformat()

    text_body = (
        f"Hello {data.beneficiary_name},\n\n"
        f"Your next AshaSarthi visit is scheduled for {visit_date}.\n"
        f"Available: {yes_url}\n"
        f"Not available: {no_url}\n"
    )
    html_body = f"""<!doctype html>
<html><body style="font-family:Arial,sans-serif">
  <h2>AshaSarthi - Visit Confirmation</h2>
  <p>Hello {safe_name},</p>
  <p>Your next visit is scheduled for <b>{visit_date}</b>.</p>
  <p>Will you be available?</p>
  <p><a href="{yes_url}">Yes, I am available</a></p>
  <p><a href="{no_url}">No, I am not available</a></p>
</body></html>"""

    try:
        provider_result = send_email(
            str(data.beneficiary_email),
            "AshaSarthi - Visit Confirmation",
            text_body,
            html_body,
        )
    except Exception:
        logger.exception("Email sending failed")
        if confirmation_id is not None:
            cleanup_conn = None
            try:
                cleanup_conn = get_db_connection()
                cursor = cleanup_conn.cursor()
                cursor.execute(
                    "DELETE FROM email_confirmations WHERE id = %s",
                    (confirmation_id,),
                )
                cleanup_conn.commit()
                cursor.close()
            except Exception:
                logger.exception("Could not remove failed confirmation record")
            finally:
                if cleanup_conn is not None and cleanup_conn.is_connected():
                    cleanup_conn.close()
        raise

    return {
        "success": True,
        "message": "Confirmation email accepted by the email provider.",
        "provider_id": provider_result.get("id"),
    }


@app.post("/send-visit-email")
def send_visit_email_api(data: VisitEmailRequest):
    return create_and_send_visit_email(data)


# Compatibility route: older Flutter code may call /messages.
# It accepts the same JSON fields as /send-visit-email.
@app.post("/messages")
def send_message(data: VisitEmailRequest):
    return create_and_send_visit_email(data)


# -------------------- Beneficiary Yes/No response --------------------

def find_confirmation(token: str):
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, beneficiary_name, response, created_at
            FROM email_confirmations
            WHERE token_hash = %s
              AND created_at >= NOW() - INTERVAL 7 DAY
            """,
            (token_hash,),
        )
        record = cursor.fetchone()
        cursor.close()
        return record
    finally:
        conn.close()


@app.get("/respond", response_class=HTMLResponse)
def show_response_form(token: str, choice: str):
    if choice not in ("yes", "no"):
        raise HTTPException(status_code=400, detail="Invalid choice")

    try:
        record = find_confirmation(token)
    except Exception:
        logger.exception("Could not verify response link")
        raise HTTPException(
            status_code=503, detail="Could not verify response link"
        ) from None

    if not record:
        raise HTTPException(status_code=404, detail="Link is invalid or expired")

    if record["response"] is not None:
        return HTMLResponse("<h3>Your response has already been recorded.</h3>")

    label = "Yes, I am available" if choice == "yes" else "No, I am not available"
    safe_token = escape(token, quote=True)
    return HTMLResponse(
        f"""<!doctype html>
<html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="font-family:Arial,sans-serif;padding:30px">
  <h2>AshaSarthi Visit Confirmation</h2>
  <p>Please confirm your response:</p>
  <form method="post" action="/respond">
    <input type="hidden" name="token" value="{safe_token}">
    <input type="hidden" name="choice" value="{choice}">
    <button type="submit" style="padding:12px 20px;cursor:pointer">{label}</button>
  </form>
</body></html>"""
    )


@app.post("/respond", response_class=HTMLResponse)
def save_response(token: str = Form(...), choice: str = Form(...)):
    if choice not in ("yes", "no"):
        raise HTTPException(status_code=400, detail="Invalid choice")

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE email_confirmations
            SET response = %s, responded_at = %s
            WHERE token_hash = %s AND response IS NULL
              AND created_at >= NOW() - INTERVAL 7 DAY
            """,
            (
                choice,
                datetime.now(timezone.utc).replace(tzinfo=None),
                token_hash,
            ),
        )
        updated = cursor.rowcount
        conn.commit()
        cursor.close()

        if updated == 0:
            raise HTTPException(
                status_code=400,
                detail="Response already recorded or link expired",
            )

        return HTMLResponse(
            """<html><body style="font-family:Arial;padding:30px">
<h2>Thank you!</h2><p>Your response has been saved successfully.</p>
</body></html>"""
        )
    except HTTPException:
        raise
    except Exception:
        if conn is not None:
            conn.rollback()
        logger.exception("Response save failed")
        raise HTTPException(
            status_code=503, detail="Could not save visit response"
        ) from None
    finally:
        if conn is not None and conn.is_connected():
            conn.close()


@app.get("/visit-responses")
def get_visit_responses(x_sync_api_key: str | None = Header(default=None)):
    expected = os.getenv("SYNC_API_KEY")
    if (
        not expected
        or not x_sync_api_key
        or not secrets.compare_digest(x_sync_api_key, expected)
    ):
        raise HTTPException(
            status_code=401, detail="Missing or invalid X-Sync-API-Key"
        )

    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, beneficiary_name, beneficiary_email, next_visit_date,
                   response, created_at, responded_at
            FROM email_confirmations
            ORDER BY created_at DESC
            """
        )
        rows = cursor.fetchall()
        cursor.close()
        for row in rows:
            for key in ("next_visit_date", "created_at", "responded_at"):
                if row.get(key) is not None:
                    row[key] = row[key].isoformat()
        return rows
    finally:
        conn.close()
