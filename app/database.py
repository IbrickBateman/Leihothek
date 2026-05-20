import sqlite3

DB_NAME = "users.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password BLOB
    )
    """)

    # RFID kart -> locker eslesmesi
    c.execute("""
    CREATE TABLE IF NOT EXISTS rfid_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        rfid TEXT UNIQUE NOT NULL,
        locker_name TEXT NOT NULL
    )
    """)

    # Tarama gecmisi (scan history)
    c.execute("""
    CREATE TABLE IF NOT EXISTS rfid_scans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rfid TEXT NOT NULL,
        item_name TEXT,
        locker_name TEXT,
        result TEXT NOT NULL,
        timestamp TEXT NOT NULL
    )
    """)

    # Pico IP adresi gibi config degerleri
    c.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    conn.commit()
    conn.close()


# ===== RFID items helpers =====

def get_all_rfid_items():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, rfid, locker_name FROM rfid_items ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return [
        {"id": r[0], "name": r[1], "rfid": r[2], "locker_name": r[3]}
        for r in rows
    ]

def find_item_by_rfid(rfid):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, rfid, locker_name FROM rfid_items WHERE rfid = ?", (rfid,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "name": row[1], "rfid": row[2], "locker_name": row[3]}
    return None

def add_rfid_item(name, rfid, locker_name):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO rfid_items (name, rfid, locker_name) VALUES (?, ?, ?)",
            (name, rfid, locker_name)
        )
        conn.commit()
        new_id = c.lastrowid
        return {"id": new_id, "name": name, "rfid": rfid, "locker_name": locker_name}
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def delete_rfid_item(item_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM rfid_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()


# ===== scan history helpers =====

def add_scan(rfid, item_name, locker_name, result, timestamp):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO rfid_scans (rfid, item_name, locker_name, result, timestamp) VALUES (?, ?, ?, ?, ?)",
        (rfid, item_name, locker_name, result, timestamp)
    )
    conn.commit()
    conn.close()

def get_recent_scans(limit=30):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT rfid, item_name, locker_name, result, timestamp FROM rfid_scans ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    rows = c.fetchall()
    conn.close()
    return [
        {
            "rfid": r[0], "item_name": r[1], "locker_name": r[2],
            "result": r[3], "timestamp": r[4]
        }
        for r in rows
    ]


# ===== settings helpers =====

def get_setting(key, default=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key, value):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value)
    )
    conn.commit()
    conn.close()

