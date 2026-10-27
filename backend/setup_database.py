
from dotenv import load_dotenv
import os
import mysql.connector

load_dotenv()


def get_db():
    return mysql.connector.connect(
        host=os.environ["MYSQLHOST"],
        port=int(os.getenv("MYSQLPORT", "3306")),
        user=os.environ["MYSQLUSER"],
        password=os.environ["MYSQLPASSWORD"],
        database=os.environ["MYSQLDATABASE"],
    )


TABLES = [
    """
    CREATE TABLE IF NOT EXISTS beneficiaries (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        full_name VARCHAR(150) NOT NULL,
        email VARCHAR(254),
        phone VARCHAR(20),
        address TEXT,
        village VARCHAR(120),
        date_of_birth DATE,
        asha_worker_id BIGINT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS children (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        beneficiary_id BIGINT NOT NULL,
        full_name VARCHAR(150) NOT NULL,
        date_of_birth DATE NOT NULL,
        sex VARCHAR(20),
        birth_weight_kg DECIMAL(5,2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (beneficiary_id)
            REFERENCES beneficiaries(id)
            ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pregnancies (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        beneficiary_id BIGINT NOT NULL,
        registration_date DATE,
        last_menstrual_period DATE,
        expected_delivery_date DATE,
        pregnancy_status VARCHAR(30) DEFAULT 'ongoing',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (beneficiary_id)
            REFERENCES beneficiaries(id)
            ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS child_visits (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        child_id BIGINT NOT NULL,
        visit_date DATE NOT NULL,
        weight_kg DECIMAL(5,2),
        height_cm DECIMAL(5,2),
        immunization_notes TEXT,
        observations TEXT,
        next_visit_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (child_id)
            REFERENCES children(id)
            ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS maternal_visits (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        pregnancy_id BIGINT NOT NULL,
        visit_type VARCHAR(30) NOT NULL,
        visit_date DATE NOT NULL,
        blood_pressure VARCHAR(30),
        weight_kg DECIMAL(5,2),
        observations TEXT,
        next_visit_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (pregnancy_id)
            REFERENCES pregnancies(id)
            ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS visits (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        beneficiary_id BIGINT NOT NULL,
        visit_date DATE NOT NULL,
        visit_type VARCHAR(60),
        status VARCHAR(30) DEFAULT 'scheduled',
        notes TEXT,
        next_visit_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (beneficiary_id)
            REFERENCES beneficiaries(id)
            ON DELETE CASCADE
    )
    """
]


if __name__ == "__main__":
    conn = get_db()
    try:
        cursor = conn.cursor()
        for sql in TABLES:
            cursor.execute(sql)
        conn.commit()
        cursor.execute("SHOW TABLES")
        print("Database tables:")
        for row in cursor.fetchall():
            print("-", row[0])
        print("Database setup completed successfully!")
        cursor.close()
    finally:
        conn.close()
