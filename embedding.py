import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel, CLIPProcessor, CLIPModel
import cv2
from PIL import Image
import logging
from typing import Union, List
import os

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._load_models()
    
    def _load_models(self):
        """필요한 모델들을 로드"""
        try:
            # 텍스트 임베딩 모델 (BERT)
            self.text_tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
            self.text_model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2").to(self.device)
            
            # 이미지 임베딩 모델 (CLIP)
            self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
            
            logger.info("Models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            raise
    
    def _improve_korean_query(self, text: str) -> str:
        """한국어 검색어 개선"""
        # 한국어 검색어에 대한 개선된 표현 추가
        improvements = {
            "개": "dog, 강아지, 개, 개 사진, dog image",
            "사람": "person, 사람, 인간, 사람 사진, person image", 
            "고양이": "cat, 고양이, 고양이 사진, cat image",
            "강아지": "puppy, 강아지, 개, 강아지 사진, puppy image"
        }
        
        for key, improved in improvements.items():
            if key in text:
                return improved
        
        return text
    
    def generate_text_embedding(self, text: str) -> np.ndarray:
        """텍스트 임베딩 생성 (CLIP 사용)"""
        try:
            # 한국어 검색어 개선
            improved_text = self._improve_korean_query(text)
            
            # CLIP 텍스트 임베딩 생성
            inputs = self.clip_processor(
                text=improved_text, 
                return_tensors="pt", 
                padding=True, 
                truncation=True
            ).to(self.device)
            
            # 임베딩 생성
            with torch.no_grad():
                text_features = self.clip_model.get_text_features(**inputs)
                embedding = text_features.cpu().numpy()
            
            return embedding[0]  # (512,)
            
        except Exception as e:
            logger.error(f"Failed to generate text embedding: {e}")
            raise
    
    def generate_image_embedding(self, image_path: str) -> np.ndarray:
        """이미지 임베딩 생성"""
        try:
            # 이미지 로드 및 전처리
            image = Image.open(image_path)
            
            # 이미지 품질 개선
            image = self._enhance_image_quality(image)
            
            # RGB로 변환
            image = image.convert("RGB")
            
            # CLIP 모델이 기대하는 크기로 리사이즈 (224x224)
            if image.size != (224, 224):
                image = image.resize((224, 224), Image.Resampling.LANCZOS)
            
            inputs = self.clip_processor(images=image, return_tensors="pt").to(self.device)
            
            # 임베딩 생성
            with torch.no_grad():
                image_features = self.clip_model.get_image_features(**inputs)
                embedding = image_features.cpu().numpy()
            
            return embedding[0]  # (512,)
            
        except Exception as e:
            logger.error(f"Failed to generate image embedding: {e}")
            raise
    
    def _enhance_image_quality(self, image: Image.Image) -> Image.Image:
        """이미지 품질 개선"""
        try:
            # 이미지 형식별 품질 개선
            if image.format == 'JPEG':
                # JPEG 이미지는 이미 압축되어 있으므로 추가 처리 최소화
                pass
            elif image.format == 'PNG':
                # PNG는 무손실이므로 그대로 사용
                pass
            elif image.format == 'GIF':
                # GIF는 색상 제한이 있으므로 품질 개선 시도
                if image.mode == 'P':
                    # 팔레트 모드를 RGB로 변환
                    image = image.convert('RGB')
            elif image.format == 'WEBP':
                # WebP는 현대적이므로 그대로 사용
                pass
            else:
                # 기타 형식은 RGB로 변환
                if image.mode != 'RGB':
                    image = image.convert('RGB')
            
            # 이미지가 너무 작은 경우 확대 (최소 224x224)
            min_size = 224
            if image.size[0] < min_size or image.size[1] < min_size:
                # 비율 유지하면서 확대
                ratio = max(min_size / image.size[0], min_size / image.size[1])
                new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            return image
            
        except Exception as e:
            logger.warning(f"Image enhancement failed: {e}")
            # 실패 시 원본 반환
            return image
    
    def generate_video_embedding(self, video_path: str, max_frames: int = 10) -> np.ndarray:
        """영상 임베딩 생성 (프레임 샘플링)"""
        try:
            cap = cv2.VideoCapture(video_path)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if frame_count == 0:
                raise ValueError("Invalid video file")
            
            # 프레임 샘플링
            frame_indices = np.linspace(0, frame_count - 1, max_frames, dtype=int)
            embeddings = []
            
            for idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                
                if ret:
                    # BGR to RGB 변환
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    image = Image.fromarray(frame_rgb)
                    
                    # 프레임 임베딩 생성
                    inputs = self.clip_processor(images=image, return_tensors="pt").to(self.device)
                    
                    with torch.no_grad():
                        frame_features = self.clip_model.get_image_features(**inputs)
                        embeddings.append(frame_features.cpu().numpy()[0])
            
            cap.release()
            
            if not embeddings:
                raise ValueError("No valid frames found in video")
            
            # 프레임 임베딩들의 평균 계산
            video_embedding = np.mean(embeddings, axis=0)
            
            # 512차원으로 유지 (CLIP 이미지 임베딩 차원)
            return video_embedding  # (512,)
            
        except Exception as e:
            logger.error(f"Failed to generate video embedding: {e}")
            raise
    
    def generate_embedding(self, file_path: str, file_type: str) -> tuple[np.ndarray, str]:
        """파일 타입에 따른 임베딩 생성"""
        try:
            if file_type == "text":
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                embedding = self.generate_text_embedding(content)
                return embedding, content
            
            elif file_type == "image":
                embedding = self.generate_image_embedding(file_path)
                # 이미지의 경우 간단한 설명 생성
                content = f"Image file: {os.path.basename(file_path)}"
                return embedding, content
            
            elif file_type == "video":
                embedding = self.generate_video_embedding(file_path)
                # 영상의 경우 간단한 설명 생성
                content = f"Video file: {os.path.basename(file_path)}"
                return embedding, content
            
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
                
        except Exception as e:
            logger.error(f"Failed to generate embedding for {file_path}: {e}")
            raise

# 전역 임베딩 생성기 인스턴스
embedding_generator = EmbeddingGenerator() 