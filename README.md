# my_project

A new Flutter project.

## Getting Started

This project is a starting point for a Flutter application.

A few resources to get you started if this is your first Flutter project:

- [Learn Flutter](https://docs.flutter.dev/get-started/learn-flutter)
- [Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Flutter learning resources](https://docs.flutter.dev/reference/learning-resources)

For help getting started with Flutter development, view the
[online documentation](https://docs.flutter.dev/), which offers tutorials,
samples, guidance on mobile development, and a full API reference.

## New integrated features (September 2026)

- Supervisor ASHA payment management and payment-completed notifications.
- Beneficiary VHNC and disease fields visible in worker/supervisor views.
- In-app messaging and replies between ASHA workers, beneficiaries and supervisors.
- Notification center for workers and supervisors.
- English / Marathi / Hindi language selector.
- Flutter Web API URL support and web SQLite setup instructions.

See `FEATURES_ADDED.md` for the integration guide.

# Asha Sarthi — Email Visit Confirmation Feature

This is a standalone starter feature for sending a beneficiary a visit-confirmation email with **Yes / No** choices and an optional next-visit date. It does not include Railway deployment configuration.

## Contents
- `backend/email_feature.py`: FastAPI router for creating and viewing email invitations and recording a beneficiary's response.
- `backend/email_requirements.txt`: Python dependencies.
- `backend/.env.email.example`: environment-variable template.
- `flutter/lib/email_feature/email_confirmation_service.dart`: Flutter HTTP client.
- `flutter/lib/email_feature/email_confirmation_screen.dart`: basic Flutter screen to enter beneficiary details and send an email invitation.
- `flutter/lib/email_feature/beneficiary_response_screen.dart`: simple response screen for an app-side Yes/No response.

## Important setup notes
1. This is an integration starter, not a drop-in replacement for your existing `main.py`. Merge the router into your existing FastAPI app.
2. Install dependencies from `backend/email_requirements.txt` in your backend environment.
3. Copy `.env.email.example` settings into your private `.env` file. Never commit `.env`.
4. Configure SMTP credentials from your email provider. For Gmail, use a Google App Password (requires 2-Step Verification); do not use your regular Gmail password.
5. Add the router to your existing `main.py`:
   ```python
   from email_feature import router as email_router
   app.include_router(email_router)
   ```
   Ensure `email_feature.py` is importable from the backend folder (copy it next to `main.py` or adjust the import).
6. Configure your Flutter `baseUrl` to the URL where your API is hosted. This package contains no Railway deployment setup.

## API endpoints
- `POST /email-visits/send`: sends an email and stores an invitation in memory.
- `GET /email-visits/{token}`: fetch invitation details for a response page.
- `POST /email-visits/{token}/respond`: records `YES` or `NO`, plus an optional next-visit date.

## Prototype limitations
- Invitations are stored in process memory, so they are lost when the server restarts and are not shared across multiple server workers/devices. Before production, replace this store with a database table.
- Email response links use the API base URL and must be publicly reachable by the beneficiary.
- Protect the send endpoint with your existing authentication/authorization before production.
- Add rate limiting and email verification before real-world use.

