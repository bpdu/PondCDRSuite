import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import utils
from utils import ConfigError


class TestCalculateHash(unittest.TestCase):
    """Test hash calculation from filename + content"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_same_content_same_filename(self):
        """Same filename + same content = same hash"""
        file1 = os.path.join(self.temp_dir, "test.cdr")
        file2 = os.path.join(self.temp_dir, "test.cdr")

        with open(file1, "w") as f:
            f.write("content123")

        with open(file2, "w") as f:
            f.write("content123")

        hash1 = utils.calculate_hash(file1)
        hash2 = utils.calculate_hash(file2)

        self.assertEqual(hash1, hash2)

    def test_different_content_same_filename(self):
        """Same filename + different content = different hash"""
        file1 = os.path.join(self.temp_dir, "test.cdr")

        with open(file1, "w") as f:
            f.write("content1")
        hash1 = utils.calculate_hash(file1)

        with open(file1, "w") as f:
            f.write("content2")
        hash2 = utils.calculate_hash(file1)

        self.assertNotEqual(hash1, hash2)

    def test_same_content_different_filename(self):
        """Different filename + same content = different hash"""
        file1 = os.path.join(self.temp_dir, "test1.cdr")
        file2 = os.path.join(self.temp_dir, "test2.cdr")

        with open(file1, "w") as f:
            f.write("same content")

        with open(file2, "w") as f:
            f.write("same content")

        hash1 = utils.calculate_hash(file1)
        hash2 = utils.calculate_hash(file2)

        self.assertNotEqual(hash1, hash2)

    def test_nonexistent_file(self):
        """Hash calculation for nonexistent file returns None"""
        result = utils.calculate_hash("/nonexistent/file.cdr")
        self.assertIsNone(result)


class TestValidateConfig(unittest.TestCase):
    """Test configuration validation"""

    def test_missing_cdr_folder(self):
        """Raise ConfigError if CDR_FOLDER not set"""
        config = {}
        with self.assertRaises(ConfigError):
            utils.validate_config(config)

    def test_nonexistent_cdr_folder(self):
        """Raise ConfigError if CDR_FOLDER doesn't exist"""
        config = {"CDR_FOLDER": "/nonexistent/folder"}
        with self.assertRaises(ConfigError):
            utils.validate_config(config)

    def test_email_enabled_missing_smtp_host(self):
        """Raise ConfigError if email enabled but SMTP_HOST missing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "CDR_FOLDER": temp_dir,
                "EMAIL_SEND": "true",
                "EMAIL_FROM": "test@example.com",
                "EMAIL_TO": "recipient@example.com"
                # Missing SMTP_HOST
            }
            with self.assertRaises(ConfigError):
                utils.validate_config(config)

    def test_email_enabled_missing_email_from(self):
        """Raise ConfigError if email enabled but EMAIL_FROM missing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "CDR_FOLDER": temp_dir,
                "EMAIL_SEND": "true",
                "SMTP_HOST": "smtp.example.com",
                "EMAIL_TO": "recipient@example.com"
                # Missing EMAIL_FROM
            }
            with self.assertRaises(ConfigError):
                utils.validate_config(config)

    def test_telegram_enabled_missing_bot_token(self):
        """Raise ConfigError if Telegram enabled but BOT_TOKEN missing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "CDR_FOLDER": temp_dir,
                "TELEGRAM_SEND": "true",
                "TELEGRAM_CHAT_ID": "123456789"
                # Missing TELEGRAM_BOT_TOKEN
            }
            with self.assertRaises(ConfigError):
                utils.validate_config(config)

    def test_valid_config_email_only(self):
        """Valid config with email only doesn't raise"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "CDR_FOLDER": temp_dir,
                "EMAIL_SEND": "true",
                "SMTP_HOST": "smtp.example.com",
                "EMAIL_FROM": "sender@example.com",
                "EMAIL_TO": "recipient@example.com"
            }
            # Should not raise
            utils.validate_config(config)

    def test_valid_config_telegram_only(self):
        """Valid config with Telegram only doesn't raise"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "CDR_FOLDER": temp_dir,
                "TELEGRAM_SEND": "true",
                "TELEGRAM_BOT_TOKEN": "123456:ABC-DEF",
                "TELEGRAM_CHAT_ID": "123456789"
            }
            # Should not raise
            utils.validate_config(config)

    def test_valid_config_both_disabled(self):
        """Valid config with both notifications disabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "CDR_FOLDER": temp_dir,
                "EMAIL_SEND": "false",
                "TELEGRAM_SEND": "false"
            }
            # Should not raise
            utils.validate_config(config)


class TestBuildNotification(unittest.TestCase):
    """Test notification message building"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.cdr")
        with open(self.test_file, "w") as f:
            f.write("test content")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_notification_contains_filename(self):
        """Notification should contain filename"""
        result = utils.build_notification(self.test_file)

        self.assertEqual(result["filename"], "test.cdr")
        self.assertIn("test.cdr", result["subject"])
        self.assertIn("test.cdr", result["body"])
        self.assertIn("test.cdr", result["telegram_text"])

    def test_notification_contains_timestamp(self):
        """Notification should contain timestamp"""
        result = utils.build_notification(self.test_file)

        # Body and telegram_text should have timestamp format YYYY-MM-DD HH:MM:SS
        self.assertRegex(result["body"], r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")
        self.assertRegex(result["telegram_text"], r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")


class TestGetFiles(unittest.TestCase):
    """Test file listing from CDR_FOLDER"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_files_empty_folder(self):
        """Empty folder returns empty list"""
        files = utils.get_files(self.temp_dir)
        self.assertEqual(files, [])

    def test_get_files_with_files(self):
        """Returns list of files"""
        # Create test files
        Path(os.path.join(self.temp_dir, "file1.cdr")).touch()
        Path(os.path.join(self.temp_dir, "file2.cdr")).touch()

        files = utils.get_files(self.temp_dir)

        self.assertEqual(len(files), 2)
        self.assertTrue(any("file1.cdr" in f for f in files))
        self.assertTrue(any("file2.cdr" in f for f in files))

    def test_get_files_ignores_hidden(self):
        """Hidden files (starting with .) are ignored"""
        Path(os.path.join(self.temp_dir, "visible.cdr")).touch()
        Path(os.path.join(self.temp_dir, ".hidden.cdr")).touch()

        files = utils.get_files(self.temp_dir)

        self.assertEqual(len(files), 1)
        self.assertTrue(any("visible.cdr" in f for f in files))
        self.assertFalse(any(".hidden.cdr" in f for f in files))

    def test_get_files_ignores_subdirectories(self):
        """Subdirectories are ignored"""
        Path(os.path.join(self.temp_dir, "file.cdr")).touch()
        os.mkdir(os.path.join(self.temp_dir, "subdir"))

        files = utils.get_files(self.temp_dir)

        self.assertEqual(len(files), 1)
        self.assertTrue(any("file.cdr" in f for f in files))

    def test_get_files_sorted(self):
        """Files are returned sorted"""
        Path(os.path.join(self.temp_dir, "c.cdr")).touch()
        Path(os.path.join(self.temp_dir, "a.cdr")).touch()
        Path(os.path.join(self.temp_dir, "b.cdr")).touch()

        files = utils.get_files(self.temp_dir)
        filenames = [os.path.basename(f) for f in files]

        self.assertEqual(filenames, ["a.cdr", "b.cdr", "c.cdr"])

    def test_get_files_nonexistent_folder(self):
        """Nonexistent folder returns empty list"""
        files = utils.get_files("/nonexistent/folder")
        self.assertEqual(files, [])


class TestGetFilename(unittest.TestCase):
    """Test filename extraction from full path"""

    def test_get_filename_unix_path(self):
        """Extract filename from Unix-style path"""
        result = utils.get_filename("/path/to/file.cdr")
        self.assertEqual(result, "file.cdr")

    def test_get_filename_windows_path(self):
        """Extract filename from Windows-style path"""
        result = utils.get_filename("C:\\path\\to\\file.cdr")
        self.assertEqual(result, "file.cdr")

    def test_get_filename_no_directory(self):
        """Extract filename when no directory"""
        result = utils.get_filename("file.cdr")
        self.assertEqual(result, "file.cdr")


if __name__ == "__main__":
    unittest.main()
