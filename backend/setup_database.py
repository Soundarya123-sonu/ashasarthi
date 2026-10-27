"""Initialize AshaSarthi's Railway MySQL cloud storage table."""
from main import ensure_tables, get_db_connection

if __name__ == "__main__":
    ensure_tables()
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SHOW TABLES LIKE 'cloud_sync_records'")
        if cur.fetchone():
            print("Database setup completed: cloud_sync_records table is ready.")
        cur.close()
    finally:
        conn.close()
