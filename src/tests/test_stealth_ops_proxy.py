import sys
from unittest.mock import patch, MagicMock

# Mock dependencies that might be missing
needed_mocks = [
    'requests', 'cv2', 'ultralytics', 'PIL', 'vaderSentiment',
    'statsmodels', 'scipy', 'numpy', 'matplotlib',
    'python-louvain', 'community', 'aiohttp'
]
for module in needed_mocks:
    if module not in sys.modules:
        sys.modules[module] = MagicMock()

import unittest
import socket
import asyncio
from stealth.stealth_ops import ProxyManager, ProxyConfig, ProxyType, ProxyStatus

class TestStealthOpsProxyHealthCheck(unittest.IsolatedAsyncioTestCase):
    # Mocking ClientSession directly
    @patch('aiohttp.ClientSession')
    async def test_health_check_socket_exception(self, mock_session):
        """
        Test that health_check catches socket.gaierror and returns False without failing.
        """
        # Configure the mock to return an async context manager that raises the exception
        class AsyncContextManagerMock:
            async def __aenter__(self):
                raise socket.gaierror("Name or service not known")
            async def __aexit__(self, exc_type, exc, tb):
                pass

        # the outer session also needs to be an async context manager
        class SessionAsyncContextManager:
            async def __aenter__(self):
                # return a mock session object
                mock_session_obj = MagicMock()
                mock_session_obj.get.return_value = AsyncContextManagerMock()
                return mock_session_obj
            async def __aexit__(self, exc_type, exc, tb):
                pass

        mock_session.return_value = SessionAsyncContextManager()

        # Instantiate ProxyManager. We use an in-memory db or MagicMock to avoid disk I/O
        db_mock = MagicMock()
        manager = ProxyManager(database=db_mock)

        # Prevent the manager from doing IP validation logic that causes issues without db
        manager.ip_quality_checker = MagicMock()

        proxy = ProxyConfig(
            host="invalid.proxy.example.com",
            port=8080,
            proxy_type=ProxyType.HTTP,
            status=ProxyStatus.ACTIVE
        )

        # Mock report_failure so we can check it
        manager.report_failure = MagicMock()

        # Execute
        result = await manager.health_check(proxy)

        # Assert
        self.assertFalse(result)

        # We assert that the proxy is marked invalid by checking that report_failure was called
        # with the correct proxy object and "Network error".
        manager.report_failure.assert_called_once_with(proxy, "Network error")

if __name__ == '__main__':
    unittest.main()
