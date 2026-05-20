import sqlite3

DB_NAME = "users.db"

# Bu kullanici adi otomatik admin sayilir
ADMIN_USERNAME = "admin"

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

    # Her RFID kart = bir esya = bir dolap.
    # 'name' hem esyanin hem dolabin adi olarak kullanilir.
    c.execute("""
    CREATE TABLE IF NOT EXISTS rfid_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        rfid TEXT UNIQUE NOT NULL
    )
    """)

    # Tarama gecmisi (scan history)
    # source: 'admin' = admin panelde test okutma, 'client' = uye iade ederken okutma
    c.execute("""
    CREATE TABLE IF NOT EXISTS rfid_scans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rfid TEXT NOT NULL,
        item_name TEXT,
        result TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        source TEXT NOT NULL DEFAULT 'client'
    )
    """)

    # Migration: eski DB'de source kolonu yoksa ekle
    cols = [row[1] for row in c.execute("PRAGMA table_info(rfid_scans)").fetchall()]
    if "source" not in cols:
        c.execute("ALTER TABLE rfid_scans ADD COLUMN source TEXT NOT NULL DEFAULT 'client'")

    # Pico IP adresi gibi config degerleri
    c.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    conn.commit()
    conn.close()


# ===== role helper =====

def is_admin(username):
    return username == ADMIN_USERNAME


# ===== RFID items helpers =====

def get_all_rfid_items():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, rfid FROM rfid_items ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return [
        {"id": r[0], "name": r[1], "rfid": r[2]}
        for r in rows
    ]

def find_item_by_rfid(rfid):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, rfid FROM rfid_items WHERE rfid = ?", (rfid,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "name": row[1], "rfid": row[2]}
    return None

def find_item_by_name(name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, rfid FROM rfid_items WHERE name = ?", (name,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "name": row[1], "rfid": row[2]}
    return None

def add_rfid_item(name, rfid):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO rfid_items (name, rfid) VALUES (?, ?)",
            (name, rfid)
        )
        conn.commit()
        new_id = c.lastrowid
        return {"id": new_id, "name": name, "rfid": rfid}
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

def add_scan(rfid, item_name, result, timestamp, source="client"):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO rfid_scans (rfid, item_name, result, timestamp, source) VALUES (?, ?, ?, ?, ?)",
        (rfid, item_name, result, timestamp, source)
    )
    conn.commit()
    conn.close()

def get_recent_scans(limit=30, source=None):
    conn = get_connection()
    c = conn.cursor()
    if source:
        c.execute(
            "SELECT rfid, item_name, result, timestamp, source FROM rfid_scans "
            "WHERE source = ? ORDER BY id DESC LIMIT ?",
            (source, limit)
        )
    else:
        c.execute(
            "SELECT rfid, item_name, result, timestamp, source FROM rfid_scans "
            "ORDER BY id DESC LIMIT ?",
            (limit,)
        )
    rows = c.fetchall()
    conn.close()
    return [
        {"rfid": r[0], "item_name": r[1], "result": r[2], "timestamp": r[3], "source": r[4]}
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

