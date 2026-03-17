"""
Inteligência Visual - Análise de Imagens com Computer Vision
Implementa análise de imagens usando YOLO/ONNX para categorização semântica.

Autor: Instagram Intelligence System 2026
Versão: 1.0.0
Idioma: Português Brasileiro (pt-BR)
"""

import os
import logging
import hashlib
import requests
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Tentar importar bibliotecas de visão computacional
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

# ONNX Runtime para inferência
try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    ort = None

# Ultralytics YOLO (opcional, para quem tem instalado)
try:
    import ultralytics
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False

logger = logging.getLogger(__name__)


class CategoriaImagem(Enum):
    """Categorias semânticas de imagens"""
    LUXO = "luxo"
    VIAGEM = "viagem"
    ESPORTE = "esporte"
    SOCIAL = "social"
    TRABALHO = "trabalho"
    COMIDA = "comida"
    PETS = "pets"
    NATUREZA = "natureza"
    MODA = "moda"
    ARTE = "arte"
    TECNOLOGIA = "tecnologia"
    FAMILIA = "familia"
    FITNESS = "fitness"
    SELFIE = "selfie"
    OUTRO = "outro"


@dataclass
class ObjetoDetectado:
    """Objeto detectado em uma imagem"""
    classe: str
    classe_id: int
    confianca: float
    bbox: Tuple[float, float, float, float] = None  # x1, y1, x2, y2
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'classe': self.classe,
            'classe_id': self.classe_id,
            'confianca': round(self.confianca, 3),
            'bbox': self.bbox
        }


@dataclass
class AnaliseImagemResult:
    """Resultado da análise de uma imagem"""
    url_ou_path: str
    objetos_detectados: List[ObjetoDetectado] = field(default_factory=list)
    categorias: List[CategoriaImagem] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    descricao: str = ""
    confianca_geral: float = 0.0
    metadados: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'url_ou_path': self.url_ou_path[:100] if len(self.url_ou_path) > 100 else self.url_ou_path,
            'objetos_detectados': [o.to_dict() for o in self.objetos_detectados],
            'categorias': [c.value for c in self.categorias],
            'tags': self.tags,
            'descricao': self.descricao,
            'confianca_geral': round(self.confianca_geral, 3),
            'metadados': self.metadados
        }


@dataclass
class AnalisePerfilVisual:
    """Resultado agregado da análise visual de um perfil"""
    username: str
    total_imagens: int
    categorias_dominantes: List[str] = field(default_factory=list)
    tags_frequentes: List[str] = field(default_factory=list)
    distribuicao_categorias: Dict[str, int] = field(default_factory=dict)
    analises_individuais: List[AnaliseImagemResult] = field(default_factory=list)
    perfil_visual: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'username': self.username,
            'total_imagens': self.total_imagens,
            'categorias_dominantes': self.categorias_dominantes,
            'tags_frequentes': self.tags_frequentes[:20],  # Top 20 tags
            'distribuicao_categorias': self.distribuicao_categorias,
            'perfil_visual': self.perfil_visual,
            'analises_individuais': [a.to_dict() for a in self.analises_individuais[:10]]  # Top 10
        }


class MapeadorCategorias:
    """
    Mapeia classes de objetos detectados para categorias semânticas.
    Baseado nas 80 classes do COCO dataset.
    """
    
    # Classes COCO -> Categorias
    MAPEAMENTO = {
        # PESSOAS E SOCIAL
        'person': [CategoriaImagem.SOCIAL, CategoriaImagem.SELFIE],
        
        # VEÍCULOS / VIAGEM
        'bicycle': [CategoriaImagem.ESPORTE, CategoriaImagem.VIAGEM],
        'car': [CategoriaImagem.VIAGEM, CategoriaImagem.LUXO],
        'motorcycle': [CategoriaImagem.VIAGEM, CategoriaImagem.ESPORTE],
        'airplane': [CategoriaImagem.VIAGEM],
        'bus': [CategoriaImagem.VIAGEM],
        'train': [CategoriaImagem.VIAGEM],
        'truck': [CategoriaImagem.VIAGEM, CategoriaImagem.TRABALHO],
        'boat': [CategoriaImagem.VIAGEM, CategoriaImagem.LUXO],
        
        # ESPORTES
        'sports ball': [CategoriaImagem.ESPORTE],
        'kite': [CategoriaImagem.ESPORTE, CategoriaImagem.VIAGEM],
        'baseball bat': [CategoriaImagem.ESPORTE],
        'baseball glove': [CategoriaImagem.ESPORTE],
        'skateboard': [CategoriaImagem.ESPORTE],
        'surfboard': [CategoriaImagem.ESPORTE, CategoriaImagem.VIAGEM],
        'tennis racket': [CategoriaImagem.ESPORTE],
        'frisbee': [CategoriaImagem.ESPORTE],
        'skis': [CategoriaImagem.ESPORTE, CategoriaImagem.VIAGEM],
        'snowboard': [CategoriaImagem.ESPORTE, CategoriaImagem.VIAGEM],
        
        # ANIMAIS / PETS
        'bird': [CategoriaImagem.PETS, CategoriaImagem.NATUREZA],
        'cat': [CategoriaImagem.PETS],
        'dog': [CategoriaImagem.PETS],
        'horse': [CategoriaImagem.PETS, CategoriaImagem.ESPORTE],
        'sheep': [CategoriaImagem.NATUREZA],
        'cow': [CategoriaImagem.NATUREZA],
        'elephant': [CategoriaImagem.NATUREZA, CategoriaImagem.VIAGEM],
        'bear': [CategoriaImagem.NATUREZA],
        'zebra': [CategoriaImagem.NATUREZA, CategoriaImagem.VIAGEM],
        'giraffe': [CategoriaImagem.NATUREZA, CategoriaImagem.VIAGEM],
        
        # COMIDA
        'banana': [CategoriaImagem.COMIDA],
        'apple': [CategoriaImagem.COMIDA],
        'sandwich': [CategoriaImagem.COMIDA],
        'orange': [CategoriaImagem.COMIDA],
        'broccoli': [CategoriaImagem.COMIDA],
        'carrot': [CategoriaImagem.COMIDA],
        'hot dog': [CategoriaImagem.COMIDA],
        'pizza': [CategoriaImagem.COMIDA],
        'donut': [CategoriaImagem.COMIDA],
        'cake': [CategoriaImagem.COMIDA, CategoriaImagem.SOCIAL],
        'wine glass': [CategoriaImagem.COMIDA, CategoriaImagem.LUXO, CategoriaImagem.SOCIAL],
        'cup': [CategoriaImagem.COMIDA],
        'fork': [CategoriaImagem.COMIDA],
        'knife': [CategoriaImagem.COMIDA],
        'spoon': [CategoriaImagem.COMIDA],
        'bowl': [CategoriaImagem.COMIDA],
        'bottle': [CategoriaImagem.COMIDA],
        
        # TRABALHO / TECNOLOGIA
        'laptop': [CategoriaImagem.TRABALHO, CategoriaImagem.TECNOLOGIA],
        'cell phone': [CategoriaImagem.TECNOLOGIA],
        'keyboard': [CategoriaImagem.TRABALHO, CategoriaImagem.TECNOLOGIA],
        'mouse': [CategoriaImagem.TRABALHO, CategoriaImagem.TECNOLOGIA],
        'remote': [CategoriaImagem.TECNOLOGIA],
        'tv': [CategoriaImagem.TECNOLOGIA],
        'book': [CategoriaImagem.TRABALHO],
        'clock': [CategoriaImagem.TRABALHO],
        'scissors': [CategoriaImagem.TRABALHO],
        
        # LUXO / MODA
        'handbag': [CategoriaImagem.MODA, CategoriaImagem.LUXO],
        'tie': [CategoriaImagem.MODA, CategoriaImagem.TRABALHO],
        'suitcase': [CategoriaImagem.VIAGEM, CategoriaImagem.TRABALHO],
        'umbrella': [CategoriaImagem.MODA],
        'backpack': [CategoriaImagem.VIAGEM],
        
        # FITNESS
        'bench': [CategoriaImagem.FITNESS],
        'dumbbell': [CategoriaImagem.FITNESS],
        
        # OUTROS
        'potted plant': [CategoriaImagem.NATUREZA],
        'bed': [CategoriaImagem.FAMILIA],
        'dining table': [CategoriaImagem.FAMILIA, CategoriaImagem.COMIDA],
        'toilet': [CategoriaImagem.OUTRO],
        'couch': [CategoriaImagem.FAMILIA],
        'chair': [CategoriaImagem.TRABALHO, CategoriaImagem.FAMILIA],
        'vase': [CategoriaImagem.ARTE],
    }
    
    # Tags por categoria
    TAGS_CATEGORIA = {
        CategoriaImagem.LUXO: ['luxo', 'premium', 'exclusivo', 'rico', 'elite'],
        CategoriaImagem.VIAGEM: ['viagem', 'turismo', 'passeio', 'aventura', 'férias'],
        CategoriaImagem.ESPORTE: ['esporte', 'atleta', 'treino', 'competição', 'ativo'],
        CategoriaImagem.SOCIAL: ['festa', 'amigos', 'social', 'encontro', 'celebração'],
        CategoriaImagem.TRABALHO: ['trabalho', 'escritório', 'profissional', 'carreira', 'produtivo'],
        CategoriaImagem.COMIDA: ['comida', 'gastronomia', 'culinária', 'refeição', 'delícia'],
        CategoriaImagem.PETS: ['pet', 'animal', 'cachorro', 'gato', 'mascote'],
        CategoriaImagem.NATUREZA: ['natureza', 'verde', 'paisagem', 'outdoor', 'ecológico'],
        CategoriaImagem.MODA: ['moda', 'estilo', 'fashion', 'look', 'tendência'],
        CategoriaImagem.ARTE: ['arte', 'criativo', 'design', 'artístico', 'cultura'],
        CategoriaImagem.TECNOLOGIA: ['tecnologia', 'tech', 'digital', 'gadget', 'inovação'],
        CategoriaImagem.FAMILIA: ['família', 'lar', 'casa', 'amor', 'união'],
        CategoriaImagem.FITNESS: ['fitness', 'saúde', 'academia', 'corpo', 'wellness'],
        CategoriaImagem.SELFIE: ['selfie', 'eu', 'rosto', 'retrato', 'autoestima'],
    }
    
    @classmethod
    def mapear_classe_para_categorias(cls, classe: str) -> List[CategoriaImagem]:
        """Mapeia uma classe de objeto para categorias"""
        classe_lower = classe.lower()
        return cls.MAPEAMENTO.get(classe_lower, [CategoriaImagem.OUTRO])
    
    @classmethod
    def obter_tags_para_categoria(cls, categoria: CategoriaImagem) -> List[str]:
        """Retorna tags associadas a uma categoria"""
        return cls.TAGS_CATEGORIA.get(categoria, ['geral'])


class AIVision:
    """
    Módulo de Inteligência Visual.
    
    Funcionalidades:
    - Download e uso de modelo YOLOv8 Nano ONNX
    - Detecção de objetos em imagens
    - Categorização semântica
    - Geração de tags
    - Análise agregada de perfil
    """
    
    # Diretório para modelos
    MODELS_DIR = Path(__file__).parent / "models"
    YOLO_MODEL_NAME = "yolov8n.onnx"
    YOLO_MODEL_URL = "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.onnx"
    
    # Classes COCO (80 classes)
    COCO_CLASSES = [
        'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 
        'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench',
        'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 
        'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
        'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
        'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
        'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
        'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
        'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
        'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
        'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
        'toothbrush'
    ]
    
    def __init__(self, model_path: str = None):
        self.logger = logging.getLogger(__name__)
        self.model_path = model_path
        self.session = None
        self.model_loaded = False
        
        # Verificar dependências
        if not PIL_AVAILABLE:
            self.logger.warning("⚠️ PIL não disponível. Instale com: pip install Pillow")
        if not NUMPY_AVAILABLE:
            self.logger.warning("⚠️ NumPy não disponível.")
        if not ONNX_AVAILABLE:
            self.logger.warning("⚠️ ONNX Runtime não disponível. Instale com: pip install onnxruntime")
        
        # Criar diretório de modelos
        self.MODELS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Tentar carregar modelo
        if ONNX_AVAILABLE and PIL_AVAILABLE and NUMPY_AVAILABLE:
            self._load_model()
    
    def _download_model(self) -> bool:
        """Baixa o modelo YOLOv8 Nano ONNX se não existir"""
        model_path = self.MODELS_DIR / self.YOLO_MODEL_NAME
        
        if model_path.exists():
            self.logger.info(f"✅ Modelo já existe: {model_path}")
            return True
        
        self.logger.info(f"📥 Baixando modelo YOLOv8 Nano ONNX...")
        
        try:
            response = requests.get(self.YOLO_MODEL_URL, stream=True, timeout=60)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(model_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        if downloaded % (1024 * 1024) == 0:  # Log a cada 1MB
                            self.logger.info(f"  {downloaded / (1024*1024):.1f}MB / {total_size / (1024*1024):.1f}MB ({progress:.1f}%)")
            
            self.logger.info(f"✅ Modelo baixado: {model_path} ({total_size / (1024*1024):.1f}MB)")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao baixar modelo: {e}")
            return False
    
    def _load_model(self) -> bool:
        """Carrega o modelo ONNX"""
        model_path = self.model_path or (self.MODELS_DIR / self.YOLO_MODEL_NAME)
        
        if not Path(model_path).exists():
            if not self._download_model():
                self.logger.error("❌ Não foi possível baixar o modelo")
                return False
            model_path = self.MODELS_DIR / self.YOLO_MODEL_NAME
        
        try:
            self.session = ort.InferenceSession(
                str(model_path),
                providers=['CPUExecutionProvider']
            )
            self.model_loaded = True
            self.logger.info(f"✅ Modelo ONNX carregado: {model_path}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar modelo: {e}")
            return False
    
    def _preprocess_image(self, image: 'Image.Image', target_size: int = 640) -> 'np.ndarray':
        """Pré-processa imagem para entrada no YOLO"""
        # Redimensionar mantendo proporção
        ratio = min(target_size / image.width, target_size / image.height)
        new_size = (int(image.width * ratio), int(image.height * ratio))
        image_resized = image.resize(new_size, Image.BILINEAR if hasattr(Image, 'BILINEAR') else 1)
        
        # Criar imagem com padding
        new_image = Image.new('RGB', (target_size, target_size), (114, 114, 114))
        paste_x = (target_size - new_size[0]) // 2
        paste_y = (target_size - new_size[1]) // 2
        new_image.paste(image_resized, (paste_x, paste_y))
        
        # Converter para numpy e normalizar
        img_array = np.array(new_image).astype(np.float32) / 255.0
        img_array = np.transpose(img_array, (2, 0, 1))  # HWC -> CHW
        img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
        
        return img_array
    
    def _postprocess_detections(
        self, 
        outputs: 'np.ndarray', 
        conf_threshold: float = 0.5,
        iou_threshold: float = 0.45
    ) -> List[ObjetoDetectado]:
        """Processa saída do YOLO para lista de objetos"""
        # Output shape: (1, 84, 8400) para YOLOv8
        # 84 = 4 (bbox) + 80 (classes)
        
        predictions = outputs[0]  # Remove batch dimension
        predictions = np.transpose(predictions, (1, 0))  # (8400, 84)
        
        # Extrair bboxes e scores
        bboxes = predictions[:, :4]
        scores = predictions[:, 4:]
        
        # Encontrar classe com maior score para cada detecção
        class_ids = np.argmax(scores, axis=1)
        confidences = np.max(scores, axis=1)
        
        # Filtrar por confiança
        mask = confidences > conf_threshold
        bboxes = bboxes[mask]
        class_ids = class_ids[mask]
        confidences = confidences[mask]
        
        objetos = []
        for i in range(len(class_ids)):
            if class_ids[i] < len(self.COCO_CLASSES):
                objetos.append(ObjetoDetectado(
                    classe=self.COCO_CLASSES[class_ids[i]],
                    classe_id=int(class_ids[i]),
                    confianca=float(confidences[i]),
                    bbox=tuple(bboxes[i].astype(float))
                ))
        
        # Ordenar por confiança
        objetos.sort(key=lambda x: x.confianca, reverse=True)
        
        return objetos[:20]  # Limitar a 20 objetos
    
    def _download_image(self, url: str) -> Optional['Image.Image']:
        """Baixa imagem de URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            image = Image.open(BytesIO(response.content))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            return image
        except Exception as e:
            self.logger.error(f"❌ Erro ao baixar imagem: {e}")
            return None
    
    def analyze_image(self, url_or_path: str, conf_threshold: float = 0.5) -> AnaliseImagemResult:
        """
        Analisa uma imagem e retorna objetos detectados e categorias.
        
        Args:
            url_or_path: URL da imagem ou caminho local
            conf_threshold: Limiar de confiança para detecções
            
        Returns:
            AnaliseImagemResult com objetos, categorias e tags
        """
        result = AnaliseImagemResult(url_ou_path=url_or_path)
        
        # Verificar se modelo está carregado
        if not self.model_loaded:
            result.metadados['erro'] = 'Modelo não carregado'
            return result
        
        try:
            # Carregar imagem
            if url_or_path.startswith(('http://', 'https://')):
                image = self._download_image(url_or_path)
            else:
                image = Image.open(url_or_path)
                if image.mode != 'RGB':
                    image = image.convert('RGB')
            
            if image is None:
                result.metadados['erro'] = 'Não foi possível carregar imagem'
                return result
            
            # Pré-processar
            input_tensor = self._preprocess_image(image)
            
            # Inferência
            input_name = self.session.get_inputs()[0].name
            outputs = self.session.run(None, {input_name: input_tensor})
            
            # Pós-processar
            objetos = self._postprocess_detections(outputs[0], conf_threshold)
            result.objetos_detectados = objetos
            
            # Mapear para categorias
            categorias_set = set()
            tags_set = set()
            
            for obj in objetos:
                cats = MapeadorCategorias.mapear_classe_para_categorias(obj.classe)
                for cat in cats:
                    categorias_set.add(cat)
                    for tag in MapeadorCategorias.obter_tags_para_categoria(cat):
                        tags_set.add(tag)
                
                # Tag do próprio objeto
                tags_set.add(obj.classe.replace(' ', '_'))
            
            result.categorias = list(categorias_set)
            result.tags = list(tags_set)
            
            # Confiança geral
            if objetos:
                result.confianca_geral = sum(o.confianca for o in objetos) / len(objetos)
            
            # Gerar descrição
            if objetos:
                principais = [o.classe for o in objetos[:3]]
                result.descricao = f"Imagem contendo: {', '.join(principais)}"
            else:
                result.descricao = "Nenhum objeto identificado"
            
            result.metadados = {
                'largura_original': image.width,
                'altura_original': image.height,
                'total_objetos': len(objetos)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erro na análise: {e}")
            result.metadados['erro'] = str(e)
        
        return result
    
    def analyze_profile_images(
        self, 
        posts: List[Dict], 
        username: str = "",
        max_images: int = 20,
        conf_threshold: float = 0.5
    ) -> AnalisePerfilVisual:
        """
        Analisa múltiplas imagens de um perfil.
        
        Args:
            posts: Lista de posts do Instagram
            username: Nome do usuário
            max_images: Máximo de imagens para analisar
            conf_threshold: Limiar de confiança
            
        Returns:
            AnalisePerfilVisual com resultados agregados
        """
        result = AnalisePerfilVisual(
            username=username,
            total_imagens=0
        )
        
        # Coletar URLs de imagens
        urls = []
        for post in posts[:max_images]:
            url = post.get('display_url') or post.get('thumbnail_url') or post.get('image_url')
            if url:
                urls.append(url)
        
        if not urls:
            return result
        
        # Analisar cada imagem
        todas_categorias = []
        todas_tags = []
        
        for url in urls:
            self.logger.info(f"🖼️ Analisando imagem {len(result.analises_individuais) + 1}/{len(urls)}")
            analise = self.analyze_image(url, conf_threshold)
            result.analises_individuais.append(analise)
            
            todas_categorias.extend(analise.categorias)
            todas_tags.extend(analise.tags)
        
        result.total_imagens = len(result.analises_individuais)
        
        # Calcular distribuição de categorias
        for cat in todas_categorias:
            cat_str = cat.value
            result.distribuicao_categorias[cat_str] = result.distribuicao_categorias.get(cat_str, 0) + 1
        
        # Ordenar por frequência
        if result.distribuicao_categorias:
            categorias_ordenadas = sorted(
                result.distribuicao_categorias.items(),
                key=lambda x: x[1],
                reverse=True
            )
            result.categorias_dominantes = [c[0] for c in categorias_ordenadas[:5]]
        
        # Tags mais frequentes
        tag_count = {}
        for tag in todas_tags:
            tag_count[tag] = tag_count.get(tag, 0) + 1
        
        tags_ordenadas = sorted(tag_count.items(), key=lambda x: x[1], reverse=True)
        result.tags_frequentes = [t[0] for t in tags_ordenadas[:20]]
        
        # Perfil visual (insights)
        result.perfil_visual = {
            'categoria_principal': result.categorias_dominantes[0] if result.categorias_dominantes else 'indefinido',
            'diversidade_categoria': len(result.distribuicao_categorias),
            'palavras_chave': result.tags_frequentes[:5],
            'tipo_conteudo': self._inferir_tipo_conteudo(result.distribuicao_categorias)
        }
        
        return result
    
    def _inferir_tipo_conteudo(self, distribuicao: Dict[str, int]) -> str:
        """Infere o tipo predominante de conteúdo baseado nas categorias"""
        if not distribuicao:
            return 'indefinido'
        
        # Encontrar categoria dominante
        dominante = max(distribuicao, key=distribuicao.get)
        
        # Mapear para descrição
        descricoes = {
            'luxo': 'Lifestyle Premium',
            'viagem': 'Travel & Adventure',
            'esporte': 'Sports & Fitness',
            'social': 'Social Life',
            'trabalho': 'Professional',
            'comida': 'Food & Culinary',
            'pets': 'Pet Lover',
            'natureza': 'Nature & Outdoor',
            'moda': 'Fashion & Style',
            'arte': 'Art & Creative',
            'tecnologia': 'Tech',
            'familia': 'Family & Home',
            'fitness': 'Health & Wellness',
            'selfie': 'Personal/Selfie',
        }
        
        return descricoes.get(dominante, 'General')


# =============================================================================
# INSTÂNCIA GLOBAL (SINGLETON)
# =============================================================================

_vision_instance: Optional[AIVision] = None


def get_ai_vision() -> AIVision:
    """Retorna instância singleton do módulo de visão"""
    global _vision_instance
    if _vision_instance is None:
        _vision_instance = AIVision()
    return _vision_instance


# =============================================================================
# TESTE
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    vision = get_ai_vision()
    
    print("\n" + "="*60)
    print("TESTE DO MÓDULO DE INTELIGÊNCIA VISUAL")
    print("="*60 + "\n")
    
    print(f"PIL disponível: {PIL_AVAILABLE}")
    print(f"NumPy disponível: {NUMPY_AVAILABLE}")
    print(f"ONNX Runtime disponível: {ONNX_AVAILABLE}")
    print(f"Ultralytics disponível: {ULTRALYTICS_AVAILABLE}")
    print(f"Modelo carregado: {vision.model_loaded}")
    
    if vision.model_loaded:
        # Teste com imagem de exemplo
        test_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/1200px-Cat03.jpg"
        print(f"\n📷 Testando com imagem: {test_url[:50]}...")
        
        resultado = vision.analyze_image(test_url)
        
        print(f"\nResultado:")
        print(f"  Objetos detectados: {len(resultado.objetos_detectados)}")
        for obj in resultado.objetos_detectados[:5]:
            print(f"    - {obj.classe}: {obj.confianca:.2f}")
        print(f"  Categorias: {[c.value for c in resultado.categorias]}")
        print(f"  Tags: {resultado.tags[:10]}")
        print(f"  Descrição: {resultado.descricao}")
        print(f"  Confiança geral: {resultado.confianca_geral:.2f}")
    else:
        print("\n⚠️ Modelo não carregado. Instale as dependências:")
        print("  pip install pillow numpy onnxruntime")
