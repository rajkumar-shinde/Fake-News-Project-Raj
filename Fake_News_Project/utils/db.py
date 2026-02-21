import sqlite3
import pandas as pd
from datetime import datetime
import os

DB_PATH = "data/history.db"

def init_db():
    if not os.path.exists("data"):
        os.makedirs("data")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            input_type TEXT,
            input_value_short TEXT,
            prediction TEXT,
            confidence REAL,
            credibility_score INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def save_detection(input_type, input_value, prediction, confidence, credibility_score):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Truncate input value for preview
    input_value_short = (input_value[:75] + '...') if len(input_value) > 75 else input_value
    
    cursor.execute('''
        INSERT INTO history (timestamp, input_type, input_value_short, prediction, confidence, credibility_score)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (timestamp, input_type, input_value_short, prediction, confidence, credibility_score))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM history ORDER BY id DESC", conn)
    conn.close()
    return df

def delete_record(record_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM history WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
