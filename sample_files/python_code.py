"""
벡터 검색 시스템 구현 예제
"""

import numpy as np
from typing import List, Dict, Any
import json

class VectorSearchEngine:
    """벡터 검색 엔진 클래스"""
    
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.vectors = {}
        self.metadata = {}
    
    def add_vector(self, id: str, vector: np.ndarray, metadata: Dict[str, Any]):
        """벡터와 메타데이터 추가"""
        if vector.shape[0] != self.dimension:
            raise ValueError(f"Vector dimension must be {self.dimension}")
        
        self.vectors[id] = vector
        self.metadata[id] = metadata
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """코사인 유사도 계산"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        return dot_product / (norm1 * norm2)
    
    def search(self, query_vector: np.ndarray, top_k: int = 10) -> List[Dict[str, Any]]:
        """유사도 검색 수행"""
        results = []
        
        for id, vector in self.vectors.items():
            similarity = self.cosine_similarity(query_vector, vector)
            results.append({
                'id': id,
                'similarity': similarity,
                'metadata': self.metadata[id]
            })
        
        # 유사도 기준으로 정렬
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]
    
    def save(self, filepath: str):
        """벡터 데이터 저장"""
        data = {
            'dimension': self.dimension,
            'vectors': {k: v.tolist() for k, v in self.vectors.items()},
            'metadata': self.metadata
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self, filepath: str):
        """벡터 데이터 로드"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.dimension = data['dimension']
        self.vectors = {k: np.array(v) for k, v in data['vectors'].items()}
        self.metadata = data['metadata']

# 사용 예제
if __name__ == "__main__":
    # 검색 엔진 초기화
    engine = VectorSearchEngine(dimension=768)
    
    # 샘플 벡터 추가
    sample_vector1 = np.random.rand(768)
    sample_vector2 = np.random.rand(768)
    
    engine.add_vector("doc1", sample_vector1, {"title": "문서 1", "type": "text"})
    engine.add_vector("doc2", sample_vector2, {"title": "문서 2", "type": "image"})
    
    # 검색 수행
    query = np.random.rand(768)
    results = engine.search(query, top_k=5)
    
    print("검색 결과:")
    for result in results:
        print(f"ID: {result['id']}, 유사도: {result['similarity']:.4f}")
        print(f"메타데이터: {result['metadata']}")
        print() 