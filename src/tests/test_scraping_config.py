import sys
import unittest
from unittest.mock import patch, MagicMock

class TestScrapingConfig(unittest.TestCase):
    def setUp(self):
        # Mocks that will be active during tests, avoiding global side-effects
        self.mock_modules = {
            'curl_cffi': MagicMock(),
            'aiohttp': MagicMock(),
            'nodriver': MagicMock(),
            'flask': MagicMock(),
            'bs4': MagicMock(),
            'lxml': MagicMock(),
            'tenacity': MagicMock()
        }
        self.patcher = patch.dict('sys.modules', self.mock_modules)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

        # Import modules after mocking
        from core.scraping_config import get_config, ScrapingConfig, ScrapingMode
        self.get_config = get_config
        self.ScrapingConfig = ScrapingConfig
        self.ScrapingMode = ScrapingMode

    def test_get_config_returns_valid_instance(self):
        """Testa se get_config retorna uma instância válida de ScrapingConfig."""
        config = self.get_config()
        self.assertIsInstance(config, self.ScrapingConfig)
        self.assertEqual(config.mode, self.ScrapingMode.BALANCED)

    def test_get_config_is_singleton(self):
        """Testa se get_config retorna sempre a mesma instância para a configuração padrão."""
        config1 = self.get_config()
        config2 = self.get_config()
        self.assertIs(config1, config2)

    def test_get_config_safe_mode(self):
        """Testa se get_config com mode='safe' retorna a configuração correta."""
        config = self.get_config('safe')
        self.assertIsInstance(config, self.ScrapingConfig)
        self.assertEqual(config.mode, self.ScrapingMode.SAFE)

    def test_get_config_aggressive_mode(self):
        """Testa se get_config com mode='aggressive' retorna a configuração correta."""
        config = self.get_config('aggressive')
        self.assertIsInstance(config, self.ScrapingConfig)
        self.assertEqual(config.mode, self.ScrapingMode.AGGRESSIVE)

    def test_get_config_stealth_mode(self):
        """Testa se get_config com mode='stealth' retorna a configuração correta."""
        config = self.get_config('stealth')
        self.assertIsInstance(config, self.ScrapingConfig)
        self.assertEqual(config.mode, self.ScrapingMode.STEALTH)

    def test_get_config_case_insensitive(self):
        """Testa se get_config lida com o modo case-insensitive."""
        config = self.get_config('SaFe')
        self.assertIsInstance(config, self.ScrapingConfig)
        self.assertEqual(config.mode, self.ScrapingMode.SAFE)

    def test_get_config_unknown_mode_fallback(self):
        """Testa se get_config com mode desconhecido faz o fallback para 'balanced'."""
        config = self.get_config('unknown_mode')
        self.assertIsInstance(config, self.ScrapingConfig)
        self.assertEqual(config.mode, self.ScrapingMode.BALANCED)

if __name__ == '__main__':
    unittest.main()
