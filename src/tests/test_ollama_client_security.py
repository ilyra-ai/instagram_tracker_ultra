import sys
import unittest

sys.path.insert(0, ".")
from ai.ollama_client import OllamaClient

class TestOllamaClientSSRF(unittest.TestCase):
    def test_invalid_urls_raise_exception(self):
        invalid_urls = [
            "http://malicious.com",
            "http://10.0.0.1",
            "http://169.254.169.254",
            "https://evil.local",
            "ftp://localhost",
            "http://localhost@malicious.com",
            "http://[2001:db8::1]",
            "http://127.1",
            "http://2130706433",
            "http://0x7F000001",
        ]

        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValueError) as context:
                    OllamaClient(base_url=url)
                self.assertIn("URL do Ollama inválida ou insegura", str(context.exception))

    def test_valid_urls_do_not_raise(self):
        valid_urls = [
            "http://localhost",
            "http://localhost:11434",
            "http://127.0.0.1",
            "http://127.0.0.1:11434",
            "http://[::1]",
            "http://[::1]:11434",
            "https://localhost:11434"
        ]

        for url in valid_urls:
            with self.subTest(url=url):
                # Should not raise ValueError
                try:
                    client = OllamaClient(base_url=url)
                    self.assertTrue(client._is_valid_url(client.base_url))
                except ValueError:
                    self.fail(f"OllamaClient raised ValueError unexpectedly for valid URL {url}")

if __name__ == '__main__':
    unittest.main()
