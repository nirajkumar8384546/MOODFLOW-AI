import sqlite3
from datetime import datetime

def save_mood(emotion):
    conn = sqlite3.connect("moodflow.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS moods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emotion TEXT,
        timestamp TEXT
    )
    """)

    c.execute("INSERT INTO moods (emotion, timestamp) VALUES (?, ?)",
              (emotion, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()