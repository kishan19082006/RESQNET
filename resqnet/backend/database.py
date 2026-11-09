"""
SQLite Schema & Database Helper Models for RESQNET Offline Server
"""
import sqlite3

SCHEMA_SQL = '''
CREATE TABLE IF NOT EXISTS sos_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id TEXT,
    victim_name TEXT,
    phone TEXT,
    emergency_type TEXT NOT NULL,
    people_count INTEGER DEFAULT 1,
    children_count INTEGER DEFAULT 0,
    injured_count INTEGER DEFAULT 0,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    notes TEXT,
    status TEXT DEFAULT 'Pending',
    created_at TEXT NOT NULL,
    duplicate_of INTEGER DEFAULT NULL,
    merged INTEGER DEFAULT 0
);
'''

def initialize_database(db_path: str = "resqnet.db"):
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()
