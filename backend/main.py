        for row in rows:
            records.append({
                "entity": row["entity"],
                "record_id": row["record_key"],
                "payload": json.loads(row["payload"]),
                "deleted": bool(row["deleted"]),
                "updated_at": (
                    row["updated_at"].isoformat()
                    if row["updated_at"] else None
                ),
            })

        return {"success": True, "count": len(records), "records": records}
    except Exception as exc:
        print(f"Sync pull failed: {type(exc).__name__}: {exc}")
        raise HTTPException(503, "Could not read cloud records") from None
    finally:
        if conn is not None and conn.is_connected():
            conn.close()


# ---------------- EMAIL CONFIGURATION ----------------

def send_email(to_email: str, subject: str, body: str):
    """Send email through Resend's HTTPS API (works around Render Free SMTP limits)."""
    api_key = os.getenv("RESEND_API_KEY")
    # For testing, Resend's onboarding sender can be used subject to its restrictions.
    # For real beneficiary emails, verify your own domain in Resend and set EMAIL_FROM.
    from_email = os.getenv("EMAIL_FROM", "onboarding@resend.dev")

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="RESEND_API_KEY is not configured in the backend environment.",
        )

    payload = json.dumps({
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "text": body,
    }).encode("utf-8")
    request = Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "AshaSarthi-API/3.1",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=25) as response:
            result = json.loads(response.read().decode("utf-8"))
            print(f"Email accepted by Resend. id={result.get('id', 'unknown')}")
    except HTTPError as exc:
        # Log provider response for debugging, but never log the API key.
        provider_error = exc.read().decode("utf-8", errors="replace")[:1000]
        print(f"Resend API error: HTTP {exc.code}: {provider_error}")
        raise HTTPException(
            status_code=502,
            detail=f"Email provider rejected the request (HTTP {exc.code}). Check Render logs and Resend sender/recipient restrictions.",
        ) from None
    except (URLError, TimeoutError, OSError) as exc:
        print(f"Resend connection error: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=502,
            detail="Could not connect to the email provider API. Check Render logs.",
        ) from None
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"Unexpected Resend response: {type(exc).__name__}")
        raise HTTPException(
            status_code=502,
            detail="Unexpected response from the email provider.",
        ) from None


class SendVisitEmailRequest(BaseModel):
    beneficiary_email: str
    beneficiary_name: str = ""
    visit_date: str
    next_visit_date: Optional[str] = None


class VisitResponseRequest(BaseModel):
    token: str
    choice: str
    next_visit_date: Optional[str] = None


def save_visit_response(
    token: str,
    choice: str,
    next_visit_date: Optional[str] = None,
):
    if choice not in {"yes", "no"}:
        raise HTTPException(400, "choice must be yes or no")

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    conn = None

    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        cur.execute("""
            SELECT id FROM email_confirmations
            WHERE token_hash = %s
        """, (token_hash,))

        record = cur.fetchone()
        if not record:
            raise HTTPException(404, "Invalid response token")

        cur.execute("""
            UPDATE email_confirmations
            SET choice = %s,
                next_visit_date = %s,
                responded_at = %s
            WHERE token_hash = %s
        """, (
            choice,
            next_visit_date if choice == "no" else None,
            datetime.now(timezone.utc).replace(tzinfo=None),
            token_hash,
        ))

        conn.commit()
        cur.close()

        return {
            "success": True,
            "choice": choice,
            "next_visit_date": (
                next_visit_date if choice == "no" else None
            ),
        }
    except HTTPException:
        raise
    except Exception as exc:
        if conn is not None:
            conn.rollback()
        print(f"Response save failed: {type(exc).__name__}: {exc}")
        raise HTTPException(503, "Could not save visit response") from None
    finally:
        if conn is not None and conn.is_connected():
            conn.close()


@app.post("/send-visit-email")
def send_visit_email(request: SendVisitEmailRequest):
    try:
        visit_date = datetime.strptime(
            request.visit_date, "%Y-%m-%d"
        ).date()
    except ValueError:
        raise HTTPException(422, "visit_date must be YYYY-MM-DD")
