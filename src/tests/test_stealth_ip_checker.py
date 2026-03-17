import sys
import unittest
from unittest.mock import MagicMock, patch
import socket
import importlib

class TestIPQualityChecker(unittest.TestCase):
    def setUp(self):
        # Localized patching of sys.modules to avoid global pollution
        self.modules_patcher = patch.dict('sys.modules', {
            'aiohttp': MagicMock(),
            'nodriver': MagicMock()
        })
        self.modules_patcher.start()

        # Import after mocking
        import stealth.stealth_ops
        importlib.reload(stealth.stealth_ops)
        self.stealth_ops = stealth.stealth_ops

        self.IPType = self.stealth_ops.IPType
        self.ProxyConfig = self.stealth_ops.ProxyConfig
        self.ProxyType = self.stealth_ops.ProxyType

        self.checker = self.stealth_ops.IPQualityChecker()

    def tearDown(self):
        self.modules_patcher.stop()

    @patch('socket.gethostbyaddr')
    def test_check_ip_quality_datacenter(self, mock_gethostbyaddr):
        # Mock reverse DNS for AWS (matches "compute")
        mock_gethostbyaddr.return_value = ('ec2-1-2-3-4.compute-1.amazonaws.com', [], [])

        result = self.checker.check_ip_quality('1.2.3.4')

        self.assertEqual(result.ip_type, self.IPType.DATACENTER)
        self.assertFalse(result.is_safe_for_instagram)
        self.assertGreater(result.risk_score, 0.9)
        self.assertIn("IP DATACENTER DETECTADO", result.warning_message)
        self.assertIn("AÇÃO NECESSÁRIA", result.recommendation)

    @patch('socket.gethostbyaddr')
    def test_check_ip_quality_residential(self, mock_gethostbyaddr):
        # Mock reverse DNS for Comcast (matches ".comcast.")
        mock_gethostbyaddr.return_value = ('c-5-6-7-8.hsd1.ca.comcast.net', [], [])

        result = self.checker.check_ip_quality('5.6.7.8')

        self.assertEqual(result.ip_type, self.IPType.RESIDENTIAL)
        self.assertTrue(result.is_safe_for_instagram)
        self.assertEqual(result.risk_score, 0.1)

    @patch('socket.gethostbyaddr')
    def test_check_ip_quality_unknown(self, mock_gethostbyaddr):
        # Mock a host that doesn't match any patterns
        mock_gethostbyaddr.return_value = ('unknown.host.com', [], [])

        result = self.checker.check_ip_quality('9.10.11.12')

        self.assertEqual(result.ip_type, self.IPType.UNKNOWN)
        self.assertEqual(result.risk_score, 0.5)
        self.assertIn("Tipo de IP não determinado", result.warning_message)

    @patch('socket.gethostbyaddr')
    def test_check_ip_quality_dns_failure(self, mock_gethostbyaddr):
        mock_gethostbyaddr.side_effect = socket.herror()

        result = self.checker.check_ip_quality('13.14.15.16')

        self.assertEqual(result.ip_type, self.IPType.UNKNOWN)
        self.assertEqual(result.risk_score, 0.5)
        self.assertIn("Tipo de IP não determinado", result.warning_message)

    @patch('stealth.stealth_ops.IPQualityChecker._get_reverse_dns')
    def test_check_ip_quality_general_exception(self, mock_get_reverse_dns):
        # Force a generic Exception inside check_ip_quality
        mock_get_reverse_dns.side_effect = Exception("Test Exception")

        result = self.checker.check_ip_quality('17.18.19.20')

        self.assertEqual(result.ip_type, self.IPType.UNKNOWN)
        self.assertEqual(result.risk_score, 0.7)
        self.assertIn("Não foi possível verificar o IP", result.warning_message)

    @patch('socket.gethostbyaddr')
    def test_dns_cache(self, mock_gethostbyaddr):
        mock_gethostbyaddr.return_value = ('host.com', [], [])

        # Call multiple times with same IP
        self.checker._get_reverse_dns('1.1.1.1')
        self.checker._get_reverse_dns('1.1.1.1')

        # Verify gethostbyaddr was only called once
        mock_gethostbyaddr.assert_called_once_with('1.1.1.1')
        self.assertIn('1.1.1.1', self.checker._dns_cache)
        self.assertEqual(self.checker._dns_cache['1.1.1.1'], 'host.com')

    def test_validate_proxy_datacenter_provider(self):
        # Create a proxy with a known datacenter provider
        proxy = self.ProxyConfig(host='1.2.3.4', port=8080, provider='AWS')

        # Mock check_ip_quality so it returns an UNKNOWN IPResult so we can isolate
        # the provider check branch of validate_proxy_for_instagram
        mock_result = MagicMock()
        mock_result.ip_type = self.IPType.UNKNOWN

        with patch.object(self.stealth_ops.IPQualityChecker, 'check_ip_quality', return_value=mock_result):
            result = self.checker.validate_proxy_for_instagram(proxy)

            # Since check_ip_quality is mocked to UNKNOWN but the proxy has provider='AWS',
            # it should hit the datacenter providers logic and override result
            self.assertEqual(result.ip_type, self.IPType.DATACENTER)
            self.assertFalse(result.is_safe_for_instagram)
            self.assertEqual(result.risk_score, 0.99)
            self.assertIn("PROXY DE DATACENTER", result.warning_message)

    def test_validate_proxy_residential_provider(self):
        # Create a proxy with a known residential provider
        proxy = self.ProxyConfig(host='5.6.7.8', port=8080, provider='Bright Data')

        mock_result = MagicMock()
        mock_result.ip_type = self.IPType.UNKNOWN

        with patch.object(self.stealth_ops.IPQualityChecker, 'check_ip_quality', return_value=mock_result):
            result = self.checker.validate_proxy_for_instagram(proxy)

            self.assertEqual(result.ip_type, self.IPType.RESIDENTIAL)
            self.assertTrue(result.is_safe_for_instagram)
            self.assertEqual(result.risk_score, 0.05)

    @patch('socket.gethostbyaddr')
    def test_validate_proxy_fallback_to_ip(self, mock_gethostbyaddr):
        # Create a proxy without provider, should fall back to check_ip_quality
        proxy = self.ProxyConfig(host='9.10.11.12', port=8080, provider=None)
        mock_gethostbyaddr.return_value = ('ec2.amazonaws.com', [], [])

        result = self.checker.validate_proxy_for_instagram(proxy)

        self.assertEqual(result.ip_type, self.IPType.DATACENTER)
        self.assertFalse(result.is_safe_for_instagram)

    def test_emit_safety_report(self):
        report = self.checker.emit_safety_report()
        self.assertIsInstance(report, str)
        self.assertIn("RELATÓRIO DE SEGURANÇA", report)
        self.assertIn("TIPOS DE IP SEGUROS", report)

if __name__ == '__main__':
    unittest.main()
