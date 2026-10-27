# AshaSarthi Railway MySQL integration

## What this backend now stores
The `/sync/beneficiary`, `/sync/child`, `/sync/pregnancy`, and `/sync/visit` endpoints persist the full JSON record sent by the Flutter app into Railway MySQL's `cloud_sync_records` table. This flexible payload storage avoids losing fields that are present in the local SQLite tables but are not in an older SQL schema. Re-sending the same `sync_id`/record ID updates the existing row rather than creating a duplicate.

## Configure locally
1. Copy `.env.example` to `.env` inside `backend/`.
2. Set the Railway MySQL public host, public port, username, password, and database name from Railway Variables / Connect details. Do not use `127.0.0.1` for a remote Railway database.
3. Install dependencies: `python -m pip install -r requirements.txt`
4. Start from the `backend` directory: `python -m uvicorn main:app --reload`
5. Check `http://127.0.0.1:8000/health/db`. Expected: database connected.
6. Check `http://127.0.0.1:8000/docs` for the API routes.

## Deploy on Render
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Add MYSQLHOST, MYSQLPORT, MYSQLUSER, MYSQLPASSWORD, MYSQLDATABASE as Render environment variables. For a Render service connecting to Railway, use Railway's public TCP host/port unless a private network connection has specifically been configured.
- In `lib/config/server_config.dart`, set `baseUrl` to the deployed backend's HTTPS URL. Do not put database credentials in Flutter.

## Verify saved data
After the backend is connected, create or sync a test beneficiary, child, pregnancy, and visit in the app. Then open `/sync/records/beneficiary`, `/sync/records/child`, `/sync/records/pregnancy`, and `/sync/records/visit` on your backend URL. Each response should contain saved records.

## Important limitations / security
- The existing Flutter app uploads local records to the backend; this change makes the backend persist those uploaded records. Full automatic downloading/merging of records onto a second device still requires a pull-and-merge workflow in Flutter and authenticated user/worker scoping before production.
- Do not use this prototype for real beneficiary or medical records until authentication, authorization, transport security, backups, and appropriate privacy controls are verified.
- Never commit `.env`. If credentials were shared in chat or committed to Git, rotate them in Railway/email and update deployment variables.
