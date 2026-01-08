import os
import sys
import tempfile
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database


class TestDatabase(unittest.TestCase):
    """Test database operations"""

    def setUp(self):
        """Create temporary database for each test"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        os.environ["DB_NAME"] = self.temp_db.name
        database.init_db()

    def tearDown(self):
        """Remove temporary database"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_init_db_creates_table(self):
        """init_db() creates cdr_files table"""
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='cdr_files'"
        )
        result = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(result)
        self.assertEqual(result[0], "cdr_files")

    def test_init_db_idempotent(self):
        """init_db() can be called multiple times safely"""
        # First call already done in setUp
        database.init_db()  # Second call
        database.init_db()  # Third call

        # Should not raise, table should still exist
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cdr_files")
        conn.close()

    def test_insert_file_success(self):
        """insert_file() successfully inserts a record"""
        result = database.insert_file(
            filename="test.cdr",
            file_hash="abc123",
            email_sent=True,
            telegram_sent=True
        )

        self.assertTrue(result)

        # Verify in database
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cdr_files WHERE file_hash = ?", ("abc123",))
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[1], "test.cdr")  # filename
        self.assertEqual(row[2], "abc123")    # file_hash
        self.assertEqual(row[3], 1)           # email_sent
        self.assertEqual(row[4], 1)           # telegram_sent

    def test_insert_file_with_partial_success(self):
        """insert_file() correctly stores partial success status"""
        result = database.insert_file(
            filename="test.cdr",
            file_hash="abc123",
            email_sent=True,
            telegram_sent=False
        )

        self.assertTrue(result)

        # Verify in database
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT email_sent, telegram_sent FROM cdr_files WHERE file_hash = ?", ("abc123",))
        row = cursor.fetchone()
        conn.close()

        self.assertEqual(row[0], 1)  # email_sent = True
        self.assertEqual(row[1], 0)  # telegram_sent = False

    def test_insert_file_with_failure(self):
        """insert_file() correctly stores failure status"""
        result = database.insert_file(
            filename="test.cdr",
            file_hash="abc123",
            email_sent=False,
            telegram_sent=False
        )

        self.assertTrue(result)

        # Verify in database
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT email_sent, telegram_sent FROM cdr_files WHERE file_hash = ?", ("abc123",))
        row = cursor.fetchone()
        conn.close()

        self.assertEqual(row[0], 0)  # email_sent = False
        self.assertEqual(row[1], 0)  # telegram_sent = False

    def test_insert_file_replace_on_duplicate_hash(self):
        """INSERT OR REPLACE updates existing record with same hash"""
        # Insert first record
        database.insert_file(
            filename="original.cdr",
            file_hash="abc123",
            email_sent=True,
            telegram_sent=False
        )

        # Insert second record with same hash but different filename
        database.insert_file(
            filename="updated.cdr",
            file_hash="abc123",
            email_sent=True,
            telegram_sent=True
        )

        # Verify only one record exists
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cdr_files WHERE file_hash = ?", ("abc123",))
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1)

        # Verify it has the updated values
        cursor.execute("SELECT filename, telegram_sent FROM cdr_files WHERE file_hash = ?", ("abc123",))
        row = cursor.fetchone()
        conn.close()

        self.assertEqual(row[0], "updated.cdr")  # filename updated
        self.assertEqual(row[1], 1)              # telegram_sent updated

    def test_get_file_by_hash_existing(self):
        """get_file_by_hash() returns record for existing hash"""
        # Insert a record
        database.insert_file(
            filename="test.cdr",
            file_hash="abc123",
            email_sent=True,
            telegram_sent=True
        )

        # Retrieve it
        result = database.get_file_by_hash("abc123")

        self.assertIsNotNone(result)
        self.assertEqual(result[1], "test.cdr")  # filename
        self.assertEqual(result[2], "abc123")    # file_hash
        self.assertEqual(result[3], 1)           # email_sent
        self.assertEqual(result[4], 1)           # telegram_sent

    def test_get_file_by_hash_nonexistent(self):
        """get_file_by_hash() returns None for nonexistent hash"""
        result = database.get_file_by_hash("nonexistent")
        self.assertIsNone(result)

    def test_get_file_by_hash_multiple_records(self):
        """get_file_by_hash() returns correct record when multiple exist"""
        # Insert multiple records
        database.insert_file("file1.cdr", "hash1", True, True)
        database.insert_file("file2.cdr", "hash2", True, False)
        database.insert_file("file3.cdr", "hash3", False, True)

        # Retrieve specific one
        result = database.get_file_by_hash("hash2")

        self.assertIsNotNone(result)
        self.assertEqual(result[1], "file2.cdr")
        self.assertEqual(result[2], "hash2")
        self.assertEqual(result[3], 1)  # email_sent = True
        self.assertEqual(result[4], 0)  # telegram_sent = False

    def test_multiple_inserts_different_hashes(self):
        """Multiple inserts with different hashes create separate records"""
        database.insert_file("file1.cdr", "hash1", True, True)
        database.insert_file("file2.cdr", "hash2", True, False)
        database.insert_file("file3.cdr", "hash3", False, True)

        # Verify all records exist
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cdr_files")
        count = cursor.fetchone()[0]
        conn.close()

        self.assertEqual(count, 3)

    def test_timestamp_auto_populated(self):
        """Timestamp is automatically populated on insert"""
        database.insert_file("test.cdr", "hash1", True, True)

        result = database.get_file_by_hash("hash1")
        timestamp = result[5]  # changed field

        self.assertIsNotNone(timestamp)
        self.assertIsInstance(timestamp, str)
        # Should match format: YYYY-MM-DD HH:MM:SS
        self.assertRegex(timestamp, r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")


if __name__ == "__main__":
    unittest.main()
