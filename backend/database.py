import os
import sqlite3
from datetime import datetime

try:
    import pymysql
    import pymysql.cursors
    HAS_PYMYSQL = True
except ImportError:
    HAS_PYMYSQL = False

# Database Settings from Environment or Defaults
USE_MYSQL = os.getenv("USE_MYSQL", "true").lower() in ("true", "1", "yes")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "1234")
MYSQL_DB = os.getenv("MYSQL_DB", "maths_tutor_db")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))

SQLITE_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tutor.db")
if not os.path.exists(SQLITE_DB):
    root_sqlite = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tutor.db")
    if os.path.exists(root_sqlite):
        SQLITE_DB = root_sqlite


class MySQLCursorWrapper:
    """Wraps PyMySQL cursor to provide 100% SQLite-compatible parameter substitution (?)"""
    def __init__(self, raw_cursor):
        self._cur = raw_cursor

    def execute(self, query, params=None):
        # Convert SQLite ? placeholders to MySQL %s
        clean_query = query.replace('?', '%s')
        if params is not None:
            return self._cur.execute(clean_query, params)
        return self._cur.execute(clean_query)

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    @property
    def lastrowid(self):
        return self._cur.lastrowid

    def close(self):
        return self._cur.close()


class MySQLConnectionWrapper:
    """Wraps PyMySQL connection to provide dictionary-row cursor & clean commit/close"""
    def __init__(self, raw_conn):
        self._conn = raw_conn

    def cursor(self):
        return MySQLCursorWrapper(self._conn.cursor(pymysql.cursors.DictCursor))

    def commit(self):
        return self._conn.commit()

    def close(self):
        return self._conn.close()


def get_connection():
    """
    Connects to MySQL database (Primary).
    Automatically falls back to local SQLite if MySQL service is unavailable.
    """
    if USE_MYSQL and HAS_PYMYSQL:
        try:
            raw_conn = pymysql.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DB,
                port=MYSQL_PORT,
                charset='utf8mb4',
                connect_timeout=3
            )
            return MySQLConnectionWrapper(raw_conn)
        except Exception as e:
            print(f"[MySQL Notice] Could not connect to MySQL ({e}). Falling back to SQLite.")

    # Fallback / Default: SQLite
    conn = sqlite3.connect(SQLITE_DB, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes tables in the active database engine (MySQL or SQLite)"""
    conn = get_connection()
    cursor = conn.cursor()
    is_mysql = isinstance(conn, MySQLConnectionWrapper)

    if is_mysql:
        # MySQL Table Definitions
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE,
            password VARCHAR(255) NOT NULL,
            grade VARCHAR(100) DEFAULT 'Class 10',
            role VARCHAR(50) DEFAULT 'student',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT DEFAULT 1,
            title VARCHAR(500) NOT NULL,
            is_pinned TINYINT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            chat_id INT,
            sender VARCHAR(50) NOT NULL,
            text MEDIUMTEXT NOT NULL,
            style VARCHAR(100) DEFAULT 'simple',
            image_url MEDIUMTEXT,
            image_prompt VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES chats (id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # Seed Developer Admin and Demo Student Accounts in MySQL
        default_seed_users = [
            ('Developer Admin', 'dev@mathstutor.com', 'admin', 'Developer', 'developer'),
            ('Alex', 'alex@gmail.com', '1234', 'Class 10', 'student'),
            ('Sameed', 'sameedkhan7@gmail.com', '1234', 'Class 11', 'student')
        ]
        for s_name, s_email, s_pwd, s_grade, s_role in default_seed_users:
            try:
                cursor.execute("""
                INSERT IGNORE INTO users (name, email, password, grade, role)
                VALUES (?, ?, ?, ?, ?)
                """, (s_name, s_email, s_pwd, s_grade, s_role))
            except Exception:
                pass

    else:
        # SQLite Table Definitions
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            password TEXT NOT NULL,
            grade TEXT DEFAULT 'Class 10',
            role TEXT DEFAULT 'student',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            title TEXT NOT NULL,
            is_pinned INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

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

        default_seed_users = [
            ('Developer Admin', 'dev@mathstutor.com', 'admin', 'Developer', 'developer'),
            ('Alex', 'alex@gmail.com', '1234', 'Class 10', 'student'),
            ('Sameed', 'sameedkhan7@gmail.com', '1234', 'Class 11', 'student')
        ]
        for s_name, s_email, s_pwd, s_grade, s_role in default_seed_users:
            try:
                cursor.execute("""
                INSERT OR IGNORE INTO users (name, email, password, grade, role)
                VALUES (?, ?, ?, ?, ?)
                """, (s_name, s_email, s_pwd, s_grade, s_role))
            except Exception:
                pass

    conn.commit()
    conn.close()
    active_engine = "MySQL Server (maths_tutor_db)" if is_mysql else f"SQLite ({SQLITE_DB})"
    print(f"[OK] Database initialized successfully using: {active_engine}")


if __name__ == "__main__":
    init_db()