import unittest
from unittest.mock import patch, MagicMock
import sys
import socket

# Mock dependências antes de importar o módulo
sys.modules['PIL'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['onnxruntime'] = MagicMock()
sys.modules['ultralytics'] = MagicMock()
sys.modules['requests'] = MagicMock()

from intelligence.ai_vision import AIVision

class TestAIVisionSSRF(unittest.TestCase):

    def setUp(self):
        self.vision = AIVision()
        self.vision.logger = MagicMock()

    @patch('socket.getaddrinfo')
    def test_safe_url(self, mock_getaddrinfo):
        mock_getaddrinfo.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 80))]
        self.assertTrue(self.vision._is_safe_url("https://www.google.com/image.jpg"))
        self.assertTrue(self.vision._is_safe_url("http://example.com/test.png"))

    @patch('socket.getaddrinfo')
    def test_unsafe_urls(self, mock_getaddrinfo):
        def fake_getaddrinfo(host, port):
            if host in ['localhost', '127.0.0.1']:
                return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 80))]
            if host == '[::1]' or host == '::1':
                return [(socket.AF_INET6, socket.SOCK_STREAM, 6, '', ('::1', 80, 0, 0))]
            if host == '169.254.169.254':
                return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('169.254.169.254', 80))]
            if host == '10.0.0.1':
                return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('10.0.0.1', 80))]
            return []

        mock_getaddrinfo.side_effect = fake_getaddrinfo
        self.assertFalse(self.vision._is_safe_url("http://localhost:8080/admin"))
        self.assertFalse(self.vision._is_safe_url("http://127.0.0.1/api/data"))
        self.assertFalse(self.vision._is_safe_url("http://[::1]/test"))
        self.assertFalse(self.vision._is_safe_url("http://169.254.169.254/latest/meta-data/"))
        self.assertFalse(self.vision._is_safe_url("http://10.0.0.1/internal"))
        self.assertFalse(self.vision._is_safe_url("file:///etc/passwd"))
        self.assertFalse(self.vision._is_safe_url("ftp://server.local/file"))

    @patch('socket.getaddrinfo')
    @patch('intelligence.ai_vision.requests.Session')
    def test_download_image_safe_url(self, mock_session_cls, mock_getaddrinfo):
        mock_getaddrinfo.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 80))]

        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"fake_image_content"
        mock_response.raise_for_status = MagicMock()

        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_cls.return_value = mock_session

        # Mock PIL Image.open to avoid actually parsing the fake content
        with patch('intelligence.ai_vision.Image.open') as mock_open:
            mock_img = MagicMock()
            mock_img.mode = 'RGB'
            mock_open.return_value = mock_img

            result = self.vision._download_image("https://www.google.com/image.jpg")

            self.assertIsNotNone(result)
            mock_session.get.assert_called_once()
            self.vision.logger.error.assert_not_called()

    @patch('socket.getaddrinfo')
    @patch('intelligence.ai_vision.requests.Session')
    def test_download_image_unsafe_url(self, mock_session_cls, mock_getaddrinfo):
        mock_getaddrinfo.side_effect = lambda host, port: [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 80))] if host == 'localhost' else []

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        result = self.vision._download_image("http://localhost:8080/admin")

        self.assertIsNone(result)
        mock_session.get.assert_not_called()
        self.vision.logger.error.assert_called_once()

    @patch('socket.getaddrinfo')
    @patch('intelligence.ai_vision.requests.Session')
    def test_download_image_unsafe_redirect(self, mock_session_cls, mock_getaddrinfo):
        def fake_getaddrinfo(host, port):
            if host == "example.com":
                return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 80))]
            elif host == "169.254.169.254":
                return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('169.254.169.254', 80))]
            return []

        mock_getaddrinfo.side_effect = fake_getaddrinfo

        # Initial request gets a 302 to an internal server
        mock_response_redirect = MagicMock()
        mock_response_redirect.status_code = 302
        mock_response_redirect.headers = {'Location': 'http://169.254.169.254/latest/meta-data/'}

        mock_session = MagicMock()
        mock_session.get.side_effect = [mock_response_redirect]
        mock_session_cls.return_value = mock_session

        result = self.vision._download_image("http://example.com/redirect")

        self.assertIsNone(result)
        # Session.get should have been called only once for the initial request
        self.assertEqual(mock_session.get.call_count, 1)

if __name__ == '__main__':
    unittest.main()
