import os
import sqlite3
from datetime import datetime

try:
    import pymysql
    import pymysql.cursors
    HAS_PYMYSQL = True
except ImportError:
    HAS_PYMYSQL = False

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").strip().lower()
IS_PRODUCTION = ENVIRONMENT in ("production", "prod") or bool(os.getenv("RENDER"))

# Database Settings from Environment or Defaults
USE_MYSQL = bool(os.getenv("MYSQL_HOST")) and os.getenv("USE_MYSQL", "true").lower() in ("true", "1", "yes")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "1234")

# Canonical variable is MYSQL_DB, with MYSQL_DATABASE supported as backward-compatible alias.
# Precedence: MYSQL_DB takes priority if both are present.
_raw_db = (os.getenv("MYSQL_DB") or os.getenv("MYSQL_DATABASE") or "").strip()

if IS_PRODUCTION and USE_MYSQL:
    if not _raw_db:
        raise RuntimeError(
            "FATAL DATABASE CONFIGURATION ERROR: In production with MySQL enabled, "
            "'MYSQL_DB' (or 'MYSQL_DATABASE') must be explicitly set via environment variables. "
            "Connecting to an unconfigured default database in production is prohibited."
        )
    MYSQL_DB = _raw_db
else:
    MYSQL_DB = _raw_db if _raw_db else "maths_tutor_db"

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


def build_mysql_ssl_context(is_production: bool = False):
    """
    Constructs a verified TLS SSLContext for cloud MySQL (e.g. Aiven).
    Strictly verifies both certificate validity and hostname matching.
    Never disables certificate verification (CERT_NONE) in production.
    """
    import ssl
    ca_cert_path = (
        os.getenv("MYSQL_SSL_CA") or
        os.getenv("MYSQL_CA_CERT") or
        os.getenv("AIVEN_CA_CERT")
    )

    if is_production:
        if not ca_cert_path or not ca_cert_path.strip():
            raise RuntimeError(
                "FATAL DATABASE SECURITY ERROR: Production MySQL connection requires a valid CA certificate path. "
                "Set 'MYSQL_SSL_CA' or 'MYSQL_CA_CERT' to the Aiven CA certificate file."
            )
        clean_path = ca_cert_path.strip()
        if not os.path.exists(clean_path):
            raise FileNotFoundError(
                f"FATAL DATABASE SECURITY ERROR: The configured CA certificate file does not exist: {clean_path}"
            )
        ctx = ssl.create_default_context(cafile=clean_path)
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED
        return ctx

    # Development mode: if CA cert path is explicitly provided, enforce verification
    if ca_cert_path and ca_cert_path.strip():
        clean_path = ca_cert_path.strip()
        if not os.path.exists(clean_path):
            raise FileNotFoundError(f"Configured development CA certificate file not found: {clean_path}")
        ctx = ssl.create_default_context(cafile=clean_path)
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED
        return ctx

    # Default development TLS context with system trust store
    ctx = ssl.create_default_context()
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED
    return ctx


def get_connection():
    """
    Connects to MySQL database (Primary).
    Automatically falls back to local SQLite if MySQL service is unavailable.
    """
    if USE_MYSQL and HAS_PYMYSQL:
        try:
            connect_kwargs = {
                "host": MYSQL_HOST,
                "user": MYSQL_USER,
                "password": MYSQL_PASSWORD,
                "database": MYSQL_DB,
                "port": MYSQL_PORT,
                "charset": "utf8mb4",
                "connect_timeout": 5
            }
            # Enable verified TLS SSL for cloud MySQL providers (e.g. Aiven)
            if MYSQL_HOST not in ("localhost", "127.0.0.1") or os.getenv("MYSQL_SSL", "").lower() in ("true", "1", "yes"):
                connect_kwargs["ssl"] = build_mysql_ssl_context(is_production=IS_PRODUCTION)

            raw_conn = pymysql.connect(**connect_kwargs)
            return MySQLConnectionWrapper(raw_conn)
        except Exception as e:
            if IS_PRODUCTION:
                # In production, do not silently swallow security/connection errors
                print(f"[MySQL Fatal Notice] Production MySQL connection failed: {type(e).__name__}")
                raise
            print(f"[MySQL Notice] Could not connect to MySQL ({type(e).__name__}: {e}). Falling back to SQLite.")

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
            is_verified TINYINT DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_verifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            otp_hash VARCHAR(255) NOT NULL,
            salt VARCHAR(64) NOT NULL,
            user_data MEDIUMTEXT NOT NULL,
            attempts INT DEFAULT 0,
            max_attempts INT DEFAULT 5,
            resend_count INT DEFAULT 0,
            last_sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_email_verif (email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # Migration: ensure is_verified exists on older MySQL tables
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN is_verified TINYINT DEFAULT 1")
        except Exception:
            pass

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
                INSERT IGNORE INTO users (name, email, password, grade, role, is_verified)
                VALUES (?, ?, ?, ?, ?, 1)
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
            is_verified INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            otp_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            user_data TEXT NOT NULL,
            attempts INTEGER DEFAULT 0,
            max_attempts INTEGER DEFAULT 5,
            resend_count INTEGER DEFAULT 0,
            last_sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_verif ON email_verifications(email)")

        # Migration: ensure is_verified exists on older SQLite tables
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 1")
        except Exception:
            pass

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
            image_url TEXT,
            image_prompt TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES chats (id)
        )
        """)

        # Auto-migrate SQLite if old table exists without image_url/image_prompt
        try:
            cursor.execute("ALTER TABLE messages ADD COLUMN image_url TEXT")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE messages ADD COLUMN image_prompt TEXT")
        except Exception:
            pass

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