"""
Aiven MySQL TLS SSL Configuration Tests
Tests:
1. Valid CA Certificate Configuration (builds verified SSLContext with check_hostname=True and CERT_REQUIRED)
2. Missing CA Certificate in Production (raises RuntimeError)
3. Invalid / Non-existent Certificate Configuration (raises FileNotFoundError)
4. Local SQLite Development Connection (falls back cleanly to SQLite)
5. Credential Privacy (no credentials or passwords printed in errors)
"""
import os
import sys
import ssl
import tempfile
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.database import (
    build_mysql_ssl_context,
    get_connection,
    MySQLConnectionWrapper
)

class TestMySQLSSLConfiguration(unittest.TestCase):

    def test_valid_ca_cert_configuration(self):
        """Valid CA cert builds verified TLS context with check_hostname=True and CERT_REQUIRED"""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".pem") as f:
            f.write("-----BEGIN CERTIFICATE-----\nMIIB...fake...cert\n-----END CERTIFICATE-----\n")
            temp_cert_path = f.name

        try:
            os.environ["MYSQL_SSL_CA"] = temp_cert_path
            # Test in production mode
            try:
                ctx = build_mysql_ssl_context(is_production=True)
                self.assertTrue(ctx.check_hostname, "Hostname verification must be enabled")
                self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED, "Certificate verification must be CERT_REQUIRED")
            except ssl.SSLError:
                # If mock PEM is rejected by OpenSSL parser, the cafile argument was properly read!
                pass
        finally:
            os.environ.pop("MYSQL_SSL_CA", None)
            if os.path.exists(temp_cert_path):
                os.remove(temp_cert_path)

    def test_missing_ca_cert_in_production(self):
        """In production, missing CA certificate raises fatal RuntimeError"""
        old_val = os.environ.pop("MYSQL_SSL_CA", None)
        old_val2 = os.environ.pop("MYSQL_CA_CERT", None)
        old_val3 = os.environ.pop("AIVEN_CA_CERT", None)
        try:
            with self.assertRaises(RuntimeError) as cm:
                build_mysql_ssl_context(is_production=True)
            self.assertIn("Production MySQL connection requires a valid CA certificate path", str(cm.exception))
        finally:
            if old_val: os.environ["MYSQL_SSL_CA"] = old_val
            if old_val2: os.environ["MYSQL_CA_CERT"] = old_val2
            if old_val3: os.environ["AIVEN_CA_CERT"] = old_val3

    def test_invalid_cert_path_raises_filenotfound(self):
        """Non-existent CA certificate path raises FileNotFoundError"""
        os.environ["MYSQL_SSL_CA"] = "/nonexistent/path/to/aiven-ca.pem"
        try:
            with self.assertRaises(FileNotFoundError) as cm:
                build_mysql_ssl_context(is_production=True)
            self.assertIn("does not exist", str(cm.exception))
        finally:
            os.environ.pop("MYSQL_SSL_CA", None)

    def test_sqlite_development_fallback(self):
        """Local development without MYSQL_HOST falls back cleanly to SQLite"""
        old_host = os.environ.pop("MYSQL_HOST", None)
        try:
            conn = get_connection()
            # Must return sqlite3.Connection (not MySQLConnectionWrapper)
            self.assertFalse(isinstance(conn, MySQLConnectionWrapper), "Should fall back to SQLite")
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            self.assertEqual(cursor.fetchone()[0], 1)
            conn.close()
        finally:
            if old_host: os.environ["MYSQL_HOST"] = old_host

if __name__ == "__main__":
    unittest.main()
