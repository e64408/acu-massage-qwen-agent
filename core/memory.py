import sqlite3
from pathlib import Path
from collections import Counter
import pandas as pd

DB_DIR = Path(__file__).parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_FILE = DB_DIR / "health_memory.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        create_time TEXT,
        symptom TEXT,
        acupoints TEXT,
        robot_path TEXT
    )""")
    conn.commit()
    conn.close()

def save_record(time_str, symptom, point_names, path_json):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO history(create_time,symptom,acupoints,robot_path) VALUES (?,?,?,?)",
        (time_str, symptom, ",".join(point_names), path_json)
    )
    conn.commit()
    conn.close()

def get_statistics():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("SELECT acupoints FROM history", conn)
    conn.close()
    cnt = Counter()
    for text in df["acupoints"].dropna():
        items = text.split(",")
        cnt.update([i.strip() for i in items if i.strip()])
    return cnt.most_common()
