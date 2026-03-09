import unittest
from unittest.mock import MagicMock, patch
import base64
import os
import sys

# Mock modules that are missing in the environment but imported in browser_manager
sys.modules['nodriver'] = MagicMock()
sys.modules['cryptography'] = MagicMock()
sys.modules['cryptography.fernet'] = MagicMock()
sys.modules['cryptography.hazmat'] = MagicMock()
sys.modules['cryptography.hazmat.primitives'] = MagicMock()
sys.modules['cryptography.hazmat.primitives.hashes'] = MagicMock()
sys.modules['cryptography.hazmat.primitives.kdf'] = MagicMock()
sys.modules['cryptography.hazmat.primitives.kdf.pbkdf2'] = MagicMock()

# Mocking modules required by core.__init__
sys.modules['curl_cffi'] = MagicMock()
sys.modules['aiohttp'] = MagicMock()
sys.modules['ultralytics'] = MagicMock()
sys.modules['flask'] = MagicMock()
sys.modules['bs4'] = MagicMock()
sys.modules['vaderSentiment'] = MagicMock()
sys.modules['tenacity'] = MagicMock()
sys.modules['eventlet'] = MagicMock()
sys.modules['flask_socketio'] = MagicMock()

# Import the class to be tested
import core.browser_manager
from core.browser_manager import CookieEncryptor

class TestCookieEncryptor(unittest.TestCase):
    def setUp(self):
        self.password = "test_password"
        self.test_data = "sensitive_data_123"

    def test_fallback_encryption_decryption(self):
        """Test encryption and decryption when cryptography is NOT available (fallback to base64)"""
        # Ensure we are testing the fallback path
        with patch('core.browser_manager.CRYPTO_AVAILABLE', False):
            encryptor = CookieEncryptor(self.password)
            self.assertIsNone(encryptor.fernet)

            encrypted = encryptor.encrypt(self.test_data)
            # In fallback it should be base64
            expected_encrypted = base64.b64encode(self.test_data.encode())
            self.assertEqual(encrypted, expected_encrypted)

            decrypted = encryptor.decrypt(encrypted)
            self.assertEqual(decrypted, self.test_data)

    def test_fernet_encryption_decryption(self):
        """Test encryption and decryption when cryptography IS available"""
        with patch('core.browser_manager.CRYPTO_AVAILABLE', True):
            # Setup mocks for cryptography components
            mock_fernet_class = MagicMock()
            mock_kdf_class = MagicMock()
            mock_hashes = MagicMock()

            with patch('core.browser_manager.Fernet', mock_fernet_class, create=True), \
                 patch('core.browser_manager.PBKDF2HMAC', mock_kdf_class, create=True), \
                 patch('core.browser_manager.hashes', mock_hashes, create=True):

                # Setup mock behavior
                mock_kdf = MagicMock()
                mock_kdf_class.return_value = mock_kdf
                mock_kdf.derive.return_value = b"derived_key_32_bytes_long_enough_"

                mock_fernet_instance = MagicMock()
                mock_fernet_class.return_value = mock_fernet_instance
                mock_fernet_instance.encrypt.return_value = b"encrypted_bytes"
                mock_fernet_instance.decrypt.return_value = self.test_data.encode()

                # Initialize encryptor
                salt = os.urandom(16)
                encryptor = CookieEncryptor(self.password, salt=salt)

                # Verify KDF call
                mock_kdf_class.assert_called_once()
                args, kwargs = mock_kdf_class.call_args
                self.assertEqual(kwargs['salt'], salt)

                # Test encrypt
                encrypted = encryptor.encrypt(self.test_data)
                self.assertEqual(encrypted, b"encrypted_bytes")
                mock_fernet_instance.encrypt.assert_called_with(self.test_data.encode())

                # Test decrypt
                decrypted = encryptor.decrypt(b"encrypted_bytes")
                self.assertEqual(decrypted, self.test_data)
                mock_fernet_instance.decrypt.assert_called_with(b"encrypted_bytes")

    def test_consistency(self):
        """Test that encryption followed by decryption returns the original string (regardless of mode)"""
        # We need to make sure we're in a consistent mode
        # Case 1: Fallback mode
        with patch('core.browser_manager.CRYPTO_AVAILABLE', False):
            encryptor = CookieEncryptor(self.password)
            encrypted = encryptor.encrypt(self.test_data)
            decrypted = encryptor.decrypt(encrypted)
            self.assertEqual(decrypted, self.test_data)

        # Case 2: Crypto mode (using mocks)
        with patch('core.browser_manager.CRYPTO_AVAILABLE', True):
            mock_fernet_class = MagicMock()
            mock_kdf_class = MagicMock()
            mock_hashes = MagicMock()

            with patch('core.browser_manager.Fernet', mock_fernet_class, create=True), \
                 patch('core.browser_manager.PBKDF2HMAC', mock_kdf_class, create=True), \
                 patch('core.browser_manager.hashes', mock_hashes, create=True):

                mock_kdf = MagicMock()
                mock_kdf_class.return_value = mock_kdf
                mock_kdf.derive.return_value = b"derived_key_32_bytes_long_enough_"

                # Important: Fernet instance must be consistent
                mock_fernet_instance = MagicMock()
                mock_fernet_class.return_value = mock_fernet_instance

                # Simulating actual encryption/decryption by Fernet
                storage = {}
                def fake_encrypt(data):
                    token = b"token_" + data
                    storage[token] = data
                    return token
                def fake_decrypt(token):
                    return storage[token]

                mock_fernet_instance.encrypt.side_effect = fake_encrypt
                mock_fernet_instance.decrypt.side_effect = fake_decrypt

                encryptor = CookieEncryptor(self.password)
                encrypted = encryptor.encrypt(self.test_data)
                decrypted = encryptor.decrypt(encrypted)
                self.assertEqual(decrypted, self.test_data)

    def test_different_passwords_produce_different_output_in_fallback(self):
        """
        In fallback mode, password is not used for base64.
        """
        with patch('core.browser_manager.CRYPTO_AVAILABLE', False):
            enc1 = CookieEncryptor("pass1")
            enc2 = CookieEncryptor("pass2")
            self.assertEqual(enc1.encrypt(self.test_data), enc2.encrypt(self.test_data))

    def test_salt_persistence(self):
        """Test that salt is generated if not provided and can be retrieved"""
        with patch('core.browser_manager.CRYPTO_AVAILABLE', True):
            # Setup mock behavior
            mock_kdf_class = MagicMock()
            mock_kdf = MagicMock()
            mock_kdf_class.return_value = mock_kdf
            mock_kdf.derive.return_value = b"derived_key_32_bytes_long_enough_"

            with patch('core.browser_manager.PBKDF2HMAC', mock_kdf_class, create=True), \
                 patch('core.browser_manager.Fernet', create=True), \
                 patch('core.browser_manager.hashes', create=True):
                encryptor = CookieEncryptor(self.password)
                salt = encryptor.get_salt()
                self.assertIsInstance(salt, bytes)
                self.assertEqual(len(salt), 16)

                # Test with provided salt
                provided_salt = b"0123456789abcdef"
                encryptor2 = CookieEncryptor(self.password, salt=provided_salt)
                self.assertEqual(encryptor2.get_salt(), provided_salt)

if __name__ == "__main__":
    unittest.main()
