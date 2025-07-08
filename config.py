import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "vectordb")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "files")
    ELASTICSEARCH_INDEX = os.getenv("ELASTICSEARCH_INDEX", "files")
    
    # 새로운 설정 추가
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "100"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "app.log")
    
    # 지원하는 파일 확장자 설정
    SUPPORTED_TEXT_EXTENSIONS = ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv']
    SUPPORTED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
    SUPPORTED_VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv']
    
    # 업로드 디렉토리 생성
    os.makedirs(UPLOAD_DIR, exist_ok=True) 