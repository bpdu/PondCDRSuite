import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
import utils
from utils import ConfigError


class TestIntegrationWorkflow(unittest.TestCase):
    """Integration tests for full CDR notification workflow"""

    def setUp(self):
        """Set up temporary directories and database"""
        # Create temporary CDR folder
        self.cdr_folder = tempfile.mkdtemp()

        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        os.environ["DB_NAME"] = self.temp_db.name

        # Mock config
        self.config = {
            "CDR_FOLDER": self.cdr_folder,
            "EMAIL_SEND": "false",
            "TELEGRAM_SEND": "false"
        }

        # Initialize database
        database.init_db()

    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.cdr_folder, ignore_errors=True)
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_full_workflow_new_file(self):
        """Test complete workflow: new file -> process -> save to DB"""
        # Create test file
        test_file = os.path.join(self.cdr_folder, "test001.cdr")
        with open(test_file, "w") as f:
            f.write("CDR content 001")

        # Get new files (should find our test file)
        new_files = utils.get_new_files(self.config)
        self.assertEqual(len(new_files), 1)
        self.assertIn("test001.cdr", new_files[0])

        # Process file (notifications disabled)
        utils.process_file(test_file, self.config)

        # Verify file saved to database
        file_hash = utils.calculate_hash(test_file)
        result = database.get_file_by_hash(file_hash)

        self.assertIsNotNone(result)
        self.assertEqual(result[1], "test001.cdr")
        self.assertEqual(result[3], 1)  # email_sent = True (disabled counts as success)
        self.assertEqual(result[4], 1)  # telegram_sent = True

    def test_workflow_file_not_reprocessed(self):
        """Test that processed file is not reprocessed on next run"""
        # Create and process first file
        test_file = os.path.join(self.cdr_folder, "test002.cdr")
        with open(test_file, "w") as f:
            f.write("CDR content 002")

        # First run: should find 1 new file
        new_files = utils.get_new_files(self.config)
        self.assertEqual(len(new_files), 1)

        utils.process_file(test_file, self.config)

        # Second run: should find 0 new files
        new_files = utils.get_new_files(self.config)
        self.assertEqual(len(new_files), 0)

    def test_workflow_same_filename_different_content(self):
        """Test that same filename with different content is processed again"""
        test_file = os.path.join(self.cdr_folder, "test003.cdr")

        # Create and process first version
        with open(test_file, "w") as f:
            f.write("original content")

        new_files = utils.get_new_files(self.config)
        self.assertEqual(len(new_files), 1)
        utils.process_file(test_file, self.config)

        # Modify file content
        with open(test_file, "w") as f:
            f.write("modified content")

        # Should be detected as new file (different hash)
        new_files = utils.get_new_files(self.config)
        self.assertEqual(len(new_files), 1)

    def test_workflow_multiple_files(self):
        """Test processing multiple files in one run"""
        # Create multiple files
        for i in range(5):
            file_path = os.path.join(self.cdr_folder, f"test{i:03d}.cdr")
            with open(file_path, "w") as f:
                f.write(f"CDR content {i}")

        # Get new files
        new_files = utils.get_new_files(self.config)
        self.assertEqual(len(new_files), 5)

        # Process all files
        for file_path in new_files:
            utils.process_file(file_path, self.config)

        # Verify all files in database
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cdr_files")
        count = cursor.fetchone()[0]
        conn.close()

        self.assertEqual(count, 5)

        # Verify no new files on next run
        new_files = utils.get_new_files(self.config)
        self.assertEqual(len(new_files), 0)

    @patch("email_sender.smtplib.SMTP")
    @patch("email_sender.utils.build_notification")
    def test_workflow_with_email_enabled(self, mock_build, mock_smtp):
        """Test workflow with email notifications enabled"""
        mock_build.return_value = {
            "filename": "test.cdr",
            "subject": "Test",
            "body": "Body",
            "telegram_text": "Text"
        }
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        self.config.update({
            "EMAIL_SEND": "true",
            "SMTP_HOST": "smtp.example.com",
            "EMAIL_FROM": "sender@example.com",
            "EMAIL_TO": "recipient@example.com"
        })

        # Create test file
        test_file = os.path.join(self.cdr_folder, "test004.cdr")
        with open(test_file, "w") as f:
            f.write("CDR content 004")

        # Process file
        utils.process_file(test_file, self.config)

        # Verify email was sent
        mock_smtp.assert_called_once()

        # Verify saved to database
        file_hash = utils.calculate_hash(test_file)
        result = database.get_file_by_hash(file_hash)
        self.assertEqual(result[3], 1)  # email_sent = True

    @patch("telegram_sender.requests.post")
    @patch("telegram_sender.utils.build_notification")
    def test_workflow_with_telegram_enabled(self, mock_build, mock_post):
        """Test workflow with Telegram notifications enabled"""
        mock_build.return_value = {
            "filename": "test.cdr",
            "subject": "Test",
            "body": "Body",
            "telegram_text": "Text"
        }
        mock_response = MagicMock()
        mock_post.return_value = mock_response

        self.config.update({
            "TELEGRAM_SEND": "true",
            "TELEGRAM_BOT_TOKEN": "123456:ABC",
            "TELEGRAM_CHAT_ID": "123456789"
        })

        # Create test file
        test_file = os.path.join(self.cdr_folder, "test005.cdr")
        with open(test_file, "w") as f:
            f.write("CDR content 005")

        # Process file
        utils.process_file(test_file, self.config)

        # Verify Telegram was sent
        mock_post.assert_called_once()

        # Verify saved to database
        file_hash = utils.calculate_hash(test_file)
        result = database.get_file_by_hash(file_hash)
        self.assertEqual(result[4], 1)  # telegram_sent = True

    @patch("email_sender.smtplib.SMTP")
    @patch("email_sender.utils.build_notification")
    @patch("email_sender.time.sleep")
    def test_workflow_partial_success_email_fails(self, mock_sleep, mock_build, mock_smtp):
        """Test workflow when email fails but file is still saved to DB"""
        mock_build.return_value = {
            "filename": "test.cdr",
            "subject": "Test",
            "body": "Body",
            "telegram_text": "Text"
        }

        # Email fails all attempts
        mock_server = MagicMock()
        mock_server.send_message.side_effect = Exception("SMTP Error")
        mock_smtp.return_value.__enter__.return_value = mock_server

        self.config.update({
            "EMAIL_SEND": "true",
            "SMTP_HOST": "smtp.example.com",
            "EMAIL_FROM": "sender@example.com",
            "EMAIL_TO": "recipient@example.com"
        })

        # Create test file
        test_file = os.path.join(self.cdr_folder, "test006.cdr")
        with open(test_file, "w") as f:
            f.write("CDR content 006")

        # Process file (should not raise, despite email failure)
        utils.process_file(test_file, self.config)

        # CRITICAL: Verify file was STILL saved to database
        file_hash = utils.calculate_hash(test_file)
        result = database.get_file_by_hash(file_hash)

        self.assertIsNotNone(result)
        self.assertEqual(result[1], "test006.cdr")
        self.assertEqual(result[3], 0)  # email_sent = False

        # Verify file is NOT reprocessed on next run
        new_files = utils.get_new_files(self.config)
        self.assertEqual(len(new_files), 0)

    @patch("email_sender.smtplib.SMTP")
    @patch("telegram_sender.requests.post")
    @patch("email_sender.utils.build_notification")
    @patch("telegram_sender.utils.build_notification")
    @patch("email_sender.time.sleep")
    @patch("telegram_sender.time.sleep")
    def test_workflow_both_notifications_fail(self, tg_sleep, email_sleep, tg_build, email_build, mock_post, mock_smtp):
        """Test workflow when both notifications fail - file still saved to DB"""
        email_build.return_value = {
            "filename": "test.cdr",
            "subject": "Test",
            "body": "Body"
        }
        tg_build.return_value = {
            "telegram_text": "Text"
        }

        # Both fail
        mock_server = MagicMock()
        mock_server.send_message.side_effect = Exception("SMTP Error")
        mock_smtp.return_value.__enter__.return_value = mock_server

        mock_post.side_effect = Exception("Telegram Error")

        self.config.update({
            "EMAIL_SEND": "true",
            "TELEGRAM_SEND": "true",
            "SMTP_HOST": "smtp.example.com",
            "EMAIL_FROM": "sender@example.com",
            "EMAIL_TO": "recipient@example.com",
            "TELEGRAM_BOT_TOKEN": "123456:ABC",
            "TELEGRAM_CHAT_ID": "123456789"
        })

        # Create test file
        test_file = os.path.join(self.cdr_folder, "test007.cdr")
        with open(test_file, "w") as f:
            f.write("CDR content 007")

        # Process file
        utils.process_file(test_file, self.config)

        # CRITICAL: File MUST be saved even though both failed
        file_hash = utils.calculate_hash(test_file)
        result = database.get_file_by_hash(file_hash)

        self.assertIsNotNone(result)
        self.assertEqual(result[3], 0)  # email_sent = False
        self.assertEqual(result[4], 0)  # telegram_sent = False

        # File should NOT be reprocessed
        new_files = utils.get_new_files(self.config)
        self.assertEqual(len(new_files), 0)

    def test_validate_config_integration(self):
        """Test configuration validation with real scenarios"""
        # Valid config
        utils.validate_config(self.config)

        # Missing CDR_FOLDER
        bad_config = {"EMAIL_SEND": "false"}
        with self.assertRaises(ConfigError):
            utils.validate_config(bad_config)

        # Nonexistent CDR_FOLDER
        bad_config = {"CDR_FOLDER": "/nonexistent/path"}
        with self.assertRaises(ConfigError):
            utils.validate_config(bad_config)

    def test_workflow_with_hidden_files(self):
        """Test that hidden files (starting with .) are ignored"""
        # Create visible and hidden files
        visible_file = os.path.join(self.cdr_folder, "visible.cdr")
        hidden_file = os.path.join(self.cdr_folder, ".hidden.cdr")

        with open(visible_file, "w") as f:
            f.write("visible content")

        with open(hidden_file, "w") as f:
            f.write("hidden content")

        # Should only find visible file
        new_files = utils.get_new_files(self.config)
        self.assertEqual(len(new_files), 1)
        self.assertIn("visible.cdr", new_files[0])

    def test_workflow_sorted_files(self):
        """Test that files are processed in sorted order"""
        # Create files out of order
        for name in ["z.cdr", "a.cdr", "m.cdr"]:
            file_path = os.path.join(self.cdr_folder, name)
            with open(file_path, "w") as f:
                f.write(f"content {name}")

        new_files = utils.get_new_files(self.config)

        # Extract filenames
        filenames = [os.path.basename(f) for f in new_files]

        # Should be sorted
        self.assertEqual(filenames, ["a.cdr", "m.cdr", "z.cdr"])


if __name__ == "__main__":
    unittest.main()
