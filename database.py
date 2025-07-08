from pymongo import MongoClient
from elasticsearch import Elasticsearch
from config import Config
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.mongo_client = None
        self.elasticsearch_client = None
        self.connect()
    
    def connect(self):
        """MongoDB와 Elasticsearch에 연결"""
        try:
            # MongoDB 연결
            self.mongo_client = MongoClient(Config.MONGODB_URI)
            self.mongo_db = self.mongo_client[Config.DATABASE_NAME]
            self.mongo_collection = self.mongo_db[Config.COLLECTION_NAME]
            
            # Elasticsearch 연결
            self.elasticsearch_client = Elasticsearch([Config.ELASTICSEARCH_URL])
            
            # Elasticsearch 인덱스 생성
            self._create_elasticsearch_index()
            
            logger.info("Database connections established successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to databases: {e}")
            raise
    
    def _create_elasticsearch_index(self):
        """Elasticsearch 인덱스 생성"""
        # 인덱스가 없을 때만 생성
        if not self.elasticsearch_client.indices.exists(index=Config.ELASTICSEARCH_INDEX):
            mapping = {
                "mappings": {
                    "properties": {
                        "file_id": {"type": "keyword"},
                        "filename": {"type": "text"},
                        "file_type": {"type": "keyword"},
                        "content": {"type": "text"},
                        "vector": {
                            "type": "dense_vector",
                            "dims": 512,  # 384에서 512로 변경 (CLIP 이미지 임베딩 차원)
                            "index": True,
                            "similarity": "cosine"
                        },
                        "metadata": {"type": "object"},
                        "upload_time": {"type": "date"}
                    }
                }
            }
            
            self.elasticsearch_client.indices.create(
                index=Config.ELASTICSEARCH_INDEX,
                body=mapping
            )
            logger.info(f"Created Elasticsearch index: {Config.ELASTICSEARCH_INDEX}")
        else:
            logger.info(f"Elasticsearch index already exists: {Config.ELASTICSEARCH_INDEX}")
    
    def save_file_metadata(self, file_data):
        """파일 메타데이터를 MongoDB에 저장"""
        try:
            result = self.mongo_collection.insert_one(file_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to save file metadata: {e}")
            raise
    
    def save_vector(self, file_id, vector, content, metadata):
        """벡터를 Elasticsearch에 저장"""
        try:
            doc = {
                "file_id": file_id,
                "filename": metadata.get("filename"),
                "file_type": metadata.get("file_type"),
                "content": content,
                "vector": vector.tolist(),
                "metadata": metadata,
                "upload_time": metadata.get("upload_time")
            }
            
            self.elasticsearch_client.index(
                index=Config.ELASTICSEARCH_INDEX,
                id=file_id,
                body=doc
            )
            logger.info(f"Saved vector for file: {file_id}")
            
        except Exception as e:
            logger.error(f"Failed to save vector: {e}")
            raise
    
    def search_vectors(self, query_vector, file_type=None, limit=10, min_score=0.1):
        """벡터 검색 수행"""
        try:
            search_body = {
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'vector')",
                            "params": {"query_vector": query_vector.tolist()}
                        }
                    }
                },
                "min_score": min_score,
                "size": limit
            }
            
            # 파일 타입 필터 추가
            if file_type:
                search_body["query"]["script_score"]["query"] = {
                    "term": {"file_type": file_type}
                }
            
            response = self.elasticsearch_client.search(
                index=Config.ELASTICSEARCH_INDEX,
                body=search_body
            )
            
            return response["hits"]["hits"]
            
        except Exception as e:
            logger.error(f"Failed to search vectors: {e}")
            raise
    
    def get_file_by_id(self, file_id):
        """파일 ID로 메타데이터 조회"""
        try:
            return self.mongo_collection.find_one({"file_id": file_id})
        except Exception as e:
            logger.error(f"Failed to get file by ID: {e}")
            raise
    
    def get_all_files(self, limit=100):
        """모든 파일 목록 조회"""
        try:
            cursor = self.mongo_collection.find().limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"Failed to get all files: {e}")
            raise
    
    def delete_file(self, file_id: str):
        """파일 삭제"""
        try:
            # MongoDB에서 메타데이터 삭제
            result = self.mongo_collection.delete_one({"file_id": file_id})
            
            # Elasticsearch에서 벡터 삭제
            try:
                self.elasticsearch_client.delete(
                    index=Config.ELASTICSEARCH_INDEX,
                    id=file_id
                )
            except Exception as e:
                logger.warning(f"Failed to delete vector from Elasticsearch: {e}")
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            raise
    
    def close(self):
        """데이터베이스 연결 종료"""
        if self.mongo_client:
            self.mongo_client.close()
        logger.info("Database connections closed")

# 전역 데이터베이스 매니저 인스턴스
db_manager = DatabaseManager() 