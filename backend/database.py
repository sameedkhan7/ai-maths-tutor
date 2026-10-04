import sqlite3
from datetime import datetime

DB_NAME = "tutor.db"

def get_connection():
    """Database se connect karne ka helper"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Dict format me data read karne ke liye
    return conn

def init_db():
    """Zaroori tables create karna (Users, Chats, Messages)"""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Users Table (Student registration aur login ke liye)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        password TEXT NOT NULL,
        grade TEXT DEFAULT 'Class 10',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Chats Table (Sidebar ke chat sessions ke liye)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        title TEXT NOT NULL,
        is_pinned INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 3. Messages Table (Sawal aur AI ke step-by-step jawab ke liye)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        sender TEXT NOT NULL,
        text TEXT NOT NULL,
        style TEXT DEFAULT 'simple',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (chat_id) REFERENCES chats (id)
    )
    """)

    conn.commit()
    conn.close()
    print("[OK] Database & Tables initialized successfully!")

# App start hote hi tables create kar do
if __name__ == "__main__":
    init_db()