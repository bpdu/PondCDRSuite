import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from email_sender import send_email
from telegram_sender import send_telegram
from utils import NotificationError


class TestEmailSender(unittest.TestCase):
    """Test email sending with retry logic"""

    def setUp(self):
        """Create temporary test file"""
        self.temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".cdr")
        self.temp_file.write("test content")
        self.temp_file.close()

        self.config = {
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "user@example.com",
            "SMTP_PASSWORD": "password",
            "EMAIL_FROM": "sender@example.com",
            "EMAIL_TO": "recipient@example.com"
        }

    def tearDown(self):
        """Remove temporary file"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    @patch("email_sender.smtplib.SMTP")
    @patch("email_sender.utils.build_notification")
    def test_send_email_success_first_attempt(self, mock_build, mock_smtp):
        """Email sent successfully on first attempt"""
        mock_build.return_value = {
            "filename": "test.cdr",
            "subject": "Test Subject",
            "body": "Test Body"
        }
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = send_email(self.temp_file.name, self.config)

        self.assertTrue(result)
        mock_smtp.assert_called_once_with("smtp.example.com", 587, timeout=30)
        mock_server.send_message.assert_called_once()

    @patch("email_sender.smtplib.SMTP")
    @patch("email_sender.utils.build_notification")
    @patch("email_sender.time.sleep")  # Mock sleep to speed up tests
    def test_send_email_retry_then_success(self, mock_sleep, mock_build, mock_smtp):
        """Email fails first attempt, succeeds on retry"""
        mock_build.return_value = {
            "filename": "test.cdr",
            "subject": "Test Subject",
            "body": "Test Body"
        }

        # First call raises exception, second succeeds
        mock_server_fail = MagicMock()
        mock_server_fail.send_message.side_effect = Exception("SMTP timeout")

        mock_server_success = MagicMock()

        mock_smtp.return_value.__enter__.side_effect = [mock_server_fail, mock_server_success]

        result = send_email(self.temp_file.name, self.config)

        self.assertTrue(result)
        self.assertEqual(mock_smtp.call_count, 2)
        mock_sleep.assert_called_once_with(4.0)  # 2^2 = 4 seconds

    @patch("email_sender.smtplib.SMTP")
    @patch("email_sender.utils.build_notification")
    @patch("email_sender.time.sleep")
    def test_send_email_all_retries_fail(self, mock_sleep, mock_build, mock_smtp):
        """Email fails all 3 attempts, raises NotificationError"""
        mock_build.return_value = {
            "filename": "test.cdr",
            "subject": "Test Subject",
            "body": "Test Body"
        }

        # All attempts fail
        mock_server = MagicMock()
        mock_server.send_message.side_effect = Exception("Connection refused")
        mock_smtp.return_value.__enter__.return_value = mock_server

        with self.assertRaises(NotificationError) as context:
            send_email(self.temp_file.name, self.config)

        self.assertIn("Email sending failed", str(context.exception))
        self.assertEqual(mock_smtp.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)  # Sleep after attempts 1 and 2

    @patch("email_sender.smtplib.SMTP")
    @patch("email_sender.utils.build_notification")
    @patch("email_sender.time.sleep")
    def test_send_email_exponential_backoff(self, mock_sleep, mock_build, mock_smtp):
        """Verify exponential backoff delays: 2s, 4s, 8s"""
        mock_build.return_value = {
            "filename": "test.cdr",
            "subject": "Test Subject",
            "body": "Test Body"
        }

        mock_server = MagicMock()
        mock_server.send_message.side_effect = Exception("Temporary failure")
        mock_smtp.return_value.__enter__.return_value = mock_server

        try:
            send_email(self.temp_file.name, self.config)
        except NotificationError:
            pass

        # Verify backoff delays: 2^1=2s, 2^2=4s
        calls = mock_sleep.call_args_list
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][0][0], 2.0)  # First delay: 2 seconds
        self.assertEqual(calls[1][0][0], 4.0)  # Second delay: 4 seconds

    @patch("email_sender.smtplib.SMTP")
    @patch("email_sender.utils.build_notification")
    def test_send_email_with_starttls(self, mock_build, mock_smtp):
        """Verify STARTTLS is called for port 587"""
        mock_build.return_value = {
            "filename": "test.cdr",
            "subject": "Test Subject",
            "body": "Test Body"
        }
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        send_email(self.temp_file.name, self.config)

        # Verify starttls() was called (port 587)
        mock_server.starttls.assert_called_once()

    @patch("email_sender.smtplib.SMTP")
    @patch("email_sender.utils.build_notification")
    def test_send_email_with_authentication(self, mock_build, mock_smtp):
        """Verify SMTP authentication when credentials provided"""
        mock_build.return_value = {
            "filename": "test.cdr",
            "subject": "Test Subject",
            "body": "Test Body"
        }
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        send_email(self.temp_file.name, self.config)

        # Verify login was called with credentials
        mock_server.login.assert_called_once_with("user@example.com", "password")


class TestTelegramSender(unittest.TestCase):
    """Test Telegram sending with retry logic"""

    def setUp(self):
        """Create temporary test file"""
        self.temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".cdr")
        self.temp_file.write("test content")
        self.temp_file.close()

        self.config = {
            "TELEGRAM_BOT_TOKEN": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
            "TELEGRAM_CHAT_ID": "123456789"
        }

    def tearDown(self):
        """Remove temporary file"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    @patch("telegram_sender.requests.post")
    @patch("telegram_sender.utils.build_notification")
    def test_send_telegram_success_first_attempt(self, mock_build, mock_post):
        """Telegram sent successfully on first attempt"""
        mock_build.return_value = {
            "telegram_text": "Test message"
        }
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = send_telegram(self.temp_file.name, self.config)

        self.assertTrue(result)
        mock_post.assert_called_once()

        # Verify URL and payload
        call_args = mock_post.call_args
        self.assertIn("123456:ABC-DEF", call_args[0][0])  # URL contains token
        self.assertEqual(call_args[1]["json"]["chat_id"], "123456789")
        self.assertEqual(call_args[1]["json"]["text"], "Test message")
        self.assertEqual(call_args[1]["timeout"], 10)

    @patch("telegram_sender.requests.post")
    @patch("telegram_sender.utils.build_notification")
    @patch("telegram_sender.time.sleep")
    def test_send_telegram_retry_then_success(self, mock_sleep, mock_build, mock_post):
        """Telegram fails first attempt, succeeds on retry"""
        mock_build.return_value = {
            "telegram_text": "Test message"
        }

        # First call raises exception, second succeeds
        mock_response_success = Mock()
        mock_response_success.raise_for_status = Mock()

        mock_post.side_effect = [
            Exception("Connection timeout"),
            mock_response_success
        ]

        result = send_telegram(self.temp_file.name, self.config)

        self.assertTrue(result)
        self.assertEqual(mock_post.call_count, 2)
        mock_sleep.assert_called_once_with(4.0)  # 2^2 = 4 seconds

    @patch("telegram_sender.requests.post")
    @patch("telegram_sender.utils.build_notification")
    @patch("telegram_sender.time.sleep")
    def test_send_telegram_all_retries_fail(self, mock_sleep, mock_build, mock_post):
        """Telegram fails all 3 attempts, raises NotificationError"""
        mock_build.return_value = {
            "telegram_text": "Test message"
        }

        mock_post.side_effect = Exception("API Error")

        with self.assertRaises(NotificationError) as context:
            send_telegram(self.temp_file.name, self.config)

        self.assertIn("Telegram sending failed", str(context.exception))
        self.assertEqual(mock_post.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("telegram_sender.requests.post")
    @patch("telegram_sender.utils.build_notification")
    @patch("telegram_sender.time.sleep")
    def test_send_telegram_exponential_backoff(self, mock_sleep, mock_build, mock_post):
        """Verify exponential backoff delays: 2s, 4s"""
        mock_build.return_value = {
            "telegram_text": "Test message"
        }

        mock_post.side_effect = Exception("Temporary failure")

        try:
            send_telegram(self.temp_file.name, self.config)
        except NotificationError:
            pass

        # Verify backoff delays
        calls = mock_sleep.call_args_list
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][0][0], 2.0)  # First delay: 2 seconds
        self.assertEqual(calls[1][0][0], 4.0)  # Second delay: 4 seconds

    @patch("telegram_sender.requests.post")
    @patch("telegram_sender.utils.build_notification")
    def test_send_telegram_http_error(self, mock_build, mock_post):
        """Telegram API returns HTTP error (e.g., 401 Unauthorized)"""
        mock_build.return_value = {
            "telegram_text": "Test message"
        }

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("401 Unauthorized")
        mock_post.return_value = mock_response

        with self.assertRaises(NotificationError):
            send_telegram(self.temp_file.name, self.config)


if __name__ == "__main__":
    unittest.main()
