#!/usr/bin/env python3
"""
Vector Database Search Application Runner
"""

import uvicorn
import logging
from config import Config

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """메인 실행 함수"""
    logger.info("Starting Vector Database Search Application...")
    logger.info(f"Upload directory: {Config.UPLOAD_DIR}")
    logger.info(f"MongoDB URI: {Config.MONGODB_URI}")
    logger.info(f"Elasticsearch URL: {Config.ELASTICSEARCH_URL}")
    
    # 서버 실행
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main() 