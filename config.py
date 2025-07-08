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
    
    # 업로드 디렉토리 생성
    os.makedirs(UPLOAD_DIR, exist_ok=True) 