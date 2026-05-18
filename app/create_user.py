import sqlite3
import bcrypt

DB_NAME = "users.db"

username = "admin"
password = "1234"

hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))

conn.commit()
conn.close()

print("✅ User aangemaakt!")