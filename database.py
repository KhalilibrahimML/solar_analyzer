# database.py
import sqlite3

DB_NAME = "solar_system.db"


def init_db():
    """Initializes the database and seeds baseline evaluation historical data."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Appliances sizing input table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appliances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            power REAL NOT NULL,
            hours REAL NOT NULL,
            quantity INTEGER DEFAULT 1
        )
    """)

    # Historical Performance Monitoring Logs (Simulation data)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS generation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE,
            irradiance REAL,
            actual_generation_kwh REAL,
            load_consumed_kwh REAL
        )
    """)

    # Pre-seed history entries to show analysis/diagnostics dashboards instantly
    cursor.execute("SELECT COUNT(*) FROM generation_logs")
    if cursor.fetchone()[0] == 0:
        mock_data = [
            ("2026-06-01", 5.2, 12.5, 9.8),
            ("2026-06-02", 4.8, 11.2, 10.1),
            (
                "2026-06-03",
                4.5,
                6.2,
                9.5,
            ),  # Underperforming run (e.g. dusty/soiled panels)
            ("2026-06-04", 5.5, 13.1, 10.5),
            ("2026-06-05", 5.1, 12.2, 9.9),
            (
                "2026-06-06",
                1.8,
                3.8,
                9.0,
            ),  # Energy deficit run (stormy weather/heavy load override)
        ]
        cursor.executemany(
            """
            INSERT OR IGNORE INTO generation_logs (date, irradiance, actual_generation_kwh, load_consumed_kwh)
            VALUES (?, ?, ?, ?)
        """,
            mock_data,
        )

    conn.commit()
    conn.close()


def add_appliance(name, power, hours, quantity):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO appliances (name, power, hours, quantity)
        VALUES (?, ?, ?, ?)
    """,
        (name, power, hours, quantity),
    )
    conn.commit()
    conn.close()


def update_appliance(appliance_id, name, power, hours, quantity):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE appliances
        SET name = ?, power = ?, hours = ?, quantity = ?
        WHERE id = ?
    """,
        (name, power, hours, quantity, appliance_id),
    )
    conn.commit()
    conn.close()


def delete_appliance(appliance_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM appliances WHERE id = ?", (appliance_id,))
    conn.commit()
    conn.close()


def delete_all_appliances():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM appliances")
    conn.commit()
    conn.close()


def add_generation_log(date, irradiance, generation_kwh, load_kwh):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO generation_logs (date, irradiance, actual_generation_kwh, load_consumed_kwh)
        VALUES (?, ?, ?, ?)
    """,
        (date, irradiance, generation_kwh, load_kwh),
    )
    conn.commit()
    conn.close()


def delete_generation_log(log_date):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM generation_logs WHERE date = ?", (log_date,))
    conn.commit()
    conn.close()


def delete_all_generation_logs():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM generation_logs")
    conn.commit()
    conn.close()


def get_all_appliances():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM appliances ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": r[0], "name": r[1], "power": r[2], "hours": r[3], "quantity": r[4]}
        for r in rows
    ]


def get_generation_logs():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT date, irradiance, actual_generation_kwh, load_consumed_kwh FROM generation_logs ORDER BY date ASC"
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_recent_logs(limit=7):
    """Get the most recent log entries"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT date, actual_generation_kwh, load_consumed_kwh, irradiance FROM generation_logs ORDER BY date DESC LIMIT ?",
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return list(reversed(rows))


def get_all_logs():
    """Get all log entries for reports"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT date, actual_generation_kwh, load_consumed_kwh, irradiance FROM generation_logs ORDER BY date ASC"
    )
    rows = cursor.fetchall()
    conn.close()
    return rows
