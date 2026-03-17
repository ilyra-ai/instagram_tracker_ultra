import unittest
from unittest.mock import patch, MagicMock
import sys
import importlib

class TestAIVisionAnalyzeImage(unittest.TestCase):
    """
    Test cases for ai_vision.analyze_image.
    Uses localized mocking for dependencies to avoid polluting sys.modules.
    """

    def setUp(self):
        # Save original sys.modules to restore after tests
        self._orig_modules = sys.modules.copy()

        # Define dependencies that might be missing
        self.needed_mocks = [
            'requests', 'PIL', 'numpy', 'onnxruntime', 'ultralytics'
        ]

        for module in self.needed_mocks:
            if module not in sys.modules:
                sys.modules[module] = MagicMock()

        # Now import the module to test
        import intelligence.ai_vision as ai_vision
        importlib.reload(ai_vision)
        self.ai_vision = ai_vision

    def test_model_not_loaded(self):
        """Testa o comportamento quando o modelo não está carregado."""
        vision = self.ai_vision.AIVision()
        vision.model_loaded = False

        result = vision.analyze_image("http://dummy.url")

        self.assertEqual(result.metadados.get('erro'), 'Modelo não carregado')
        self.assertEqual(result.url_ou_path, "http://dummy.url")
        self.assertEqual(result.objetos_detectados, [])

    def test_analyze_image_download_error(self):
        """Testa o comportamento quando há erro ao baixar a imagem."""
        vision = self.ai_vision.AIVision()
        vision.model_loaded = True

        with patch.object(vision, '_download_image', return_value=None):
            result = vision.analyze_image("http://dummy.url")

        self.assertEqual(result.metadados.get('erro'), 'Não foi possível carregar imagem')
        self.assertEqual(result.url_ou_path, "http://dummy.url")
        self.assertEqual(result.objetos_detectados, [])

    def test_analyze_local_image_load_error(self):
        """Testa o comportamento quando a imagem local falha ao abrir."""
        vision = self.ai_vision.AIVision()
        vision.model_loaded = True

        # Testando a ramificação de exceção no bloco try da análise da imagem
        with patch.object(self.ai_vision, 'Image') as mock_image:
            mock_image.open.side_effect = Exception("Mock error")

            result = vision.analyze_image("local_path.jpg")

        self.assertEqual(result.metadados.get('erro'), "Mock error")
        self.assertEqual(result.url_ou_path, "local_path.jpg")

    def test_analyze_image_success(self):
        """Testa o fluxo de inferência com sucesso simulado."""
        vision = self.ai_vision.AIVision()
        vision.model_loaded = True

        # Mocks para o fluxo feliz
        mock_image = MagicMock()
        mock_image.width = 800
        mock_image.height = 600

        # Objeto detectado esperado
        expected_obj = self.ai_vision.ObjetoDetectado(
            classe='car',
            classe_id=2,
            confianca=0.95,
            bbox=(10, 10, 100, 100)
        )

        # Mock do ONNX session
        mock_session = MagicMock()
        mock_input = MagicMock()
        mock_input.name = "images"
        mock_session.get_inputs.return_value = [mock_input]
        mock_session.run.return_value = ["dummy_output"]
        vision.session = mock_session

        with patch.object(vision, '_download_image', return_value=mock_image), \
             patch.object(vision, '_preprocess_image', return_value="dummy_tensor"), \
             patch.object(vision, '_postprocess_detections', return_value=[expected_obj]):

            result = vision.analyze_image("http://dummy.url")

        # Verificações básicas de retorno
        self.assertNotIn('erro', result.metadados)
        self.assertEqual(len(result.objetos_detectados), 1)
        self.assertEqual(result.objetos_detectados[0].classe, 'car')
        self.assertEqual(result.descricao, "Imagem contendo: car")

        # Verificações de metadados e confiança
        self.assertEqual(result.metadados['total_objetos'], 1)
        self.assertEqual(result.metadados['largura_original'], 800)
        self.assertEqual(result.metadados['altura_original'], 600)
        self.assertEqual(result.confianca_geral, 0.95)

        # Verificações de categorias baseadas na classe 'car'
        self.assertIn(self.ai_vision.CategoriaImagem.VIAGEM, result.categorias)
        self.assertIn(self.ai_vision.CategoriaImagem.LUXO, result.categorias)
        self.assertIn('car', result.tags)
        self.assertIn('viagem', result.tags)

    def test_analyze_image_no_objects(self):
        """Testa o fluxo de inferência quando nenhum objeto é detectado."""
        vision = self.ai_vision.AIVision()
        vision.model_loaded = True

        mock_image = MagicMock()
        mock_image.width = 400
        mock_image.height = 400

        mock_session = MagicMock()
        mock_input = MagicMock()
        mock_input.name = "images"
        mock_session.get_inputs.return_value = [mock_input]
        mock_session.run.return_value = ["dummy_output"]
        vision.session = mock_session

        with patch.object(vision, '_download_image', return_value=mock_image), \
             patch.object(vision, '_preprocess_image', return_value="dummy_tensor"), \
             patch.object(vision, '_postprocess_detections', return_value=[]):

            result = vision.analyze_image("http://dummy.url")

        self.assertNotIn('erro', result.metadados)
        self.assertEqual(len(result.objetos_detectados), 0)
        self.assertEqual(result.descricao, "Nenhum objeto identificado")
        self.assertEqual(result.metadados['total_objetos'], 0)
        self.assertEqual(result.confianca_geral, 0.0)

    def tearDown(self):
        # Restore original sys.modules
        for module in self.needed_mocks:
            if module in sys.modules and sys.modules[module] != self._orig_modules.get(module):
                if module in self._orig_modules:
                    sys.modules[module] = self._orig_modules[module]
                else:
                    del sys.modules[module]

if __name__ == '__main__':
    unittest.main()
