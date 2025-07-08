from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import os
from typing import List, Optional
from PIL import Image
import io

from models import FileUploadResponse, SearchResponse, SearchResult, FileListResponse, FileInfo, FileType
from database import db_manager
from embedding import embedding_generator
from utils import (
    get_file_type, is_supported_file, save_uploaded_file, 
    create_file_metadata, validate_file_size, cleanup_file
)
from config import Config

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Vector Database Search API",
    description="텍스트, 이미지, 영상을 업로드하고 벡터 검색을 수행하는 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 초기화"""
    logger.info("Starting Vector Database Search API...")

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 정리"""
    logger.info("Shutting down Vector Database Search API...")
    db_manager.close()

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Vector Database Search API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/upload",
            "search": "/search",
            "files": "/files",
            "delete_file": "/files/{file_id}",
            "web_interface": "/static/index.html"
        }
    }

@app.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """파일 업로드 및 벡터 임베딩 생성"""
    try:
        # 파일 타입 검증
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        if not is_supported_file(file.filename):
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Supported types: text, image, video"
            )
        
        # 파일 저장
        file_path, file_size = await save_uploaded_file(file, Config.UPLOAD_DIR)
        
        # 파일 크기 검증
        if not validate_file_size(file_size, max_size_mb=100):
            cleanup_file(file_path)
            raise HTTPException(status_code=400, detail="File size too large (max 100MB)")
        
        # 파일 타입 결정
        file_type = get_file_type(file.filename)
        
        try:
            # 벡터 임베딩 생성
            embedding, content = embedding_generator.generate_embedding(file_path, file_type)
            
            # 파일 ID 생성
            file_id = os.path.splitext(os.path.basename(file_path))[0]
            
            # 메타데이터 생성
            metadata = create_file_metadata(
                file_id=file_id,
                original_filename=file.filename,
                saved_filepath=file_path,
                file_type=file_type,
                file_size=file_size
            )
            
            # MongoDB에 메타데이터 저장
            db_manager.save_file_metadata(metadata)
            
            # Elasticsearch에 벡터 저장
            db_manager.save_vector(file_id, embedding, content, metadata["metadata"])
            
            logger.info(f"File uploaded successfully: {file.filename}")
            
            return FileUploadResponse(
                file_id=file_id,
                filename=file.filename,
                file_type=FileType(file_type),
                file_size=file_size,
                upload_time=metadata["upload_time"],
                message="File uploaded and vectorized successfully"
            )
            
        except Exception as e:
            # 임베딩 생성 실패 시 파일 정리
            cleanup_file(file_path)
            logger.error(f"Failed to process file {file.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/search", response_model=SearchResponse)
async def search_files(
    query: str,
    min_score: float = 0.1,
    limit: int = 10,
    file_type: Optional[str] = None
):
    """벡터 검색 수행"""
    try:
        # 임베딩 생성
        embedding = embedding_generator.generate_text_embedding(query)
        
        # 데이터베이스 매니저를 통한 검색
        search_results = db_manager.search_vectors(
            query_vector=embedding,
            file_type=file_type,
            limit=limit,
            min_score=min_score
        )
        
        # 결과 처리 및 필터링
        results = []
        for hit in search_results:
            score = hit["_score"]  # cosineSimilarity는 -1~1 범위
            source = hit["_source"]
            file_type = source["file_type"]
            
            # 단순 min_score만 적용
            if score >= min_score:
                results.append(SearchResult(
                    file_id=source["file_id"],
                    filename=source["filename"],
                    file_type=FileType(file_type),
                    score=score,
                    metadata=source["metadata"]
                ))
        
        # 점수순 정렬 및 제한
        results.sort(key=lambda x: x.score, reverse=True)
        results = results[:limit]
        
        return SearchResponse(
            results=results,
            total=len(results),
            query=query
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files", response_model=FileListResponse)
async def list_files(limit: int = Query(100, ge=1, le=1000, description="조회할 파일 수")):
    """업로드된 파일 목록 조회"""
    try:
        files_data = db_manager.get_all_files(limit=limit)
        
        files = []
        for file_data in files_data:
            files.append(FileInfo(
                file_id=file_data["file_id"],
                filename=file_data["original_filename"],
                file_type=FileType(file_data["file_type"]),
                file_size=file_data["file_size"],
                upload_time=file_data["upload_time"],
                metadata=file_data["metadata"]
            ))
        
        return FileListResponse(
            files=files,
            total=len(files)
        )
        
    except Exception as e:
        logger.error(f"Failed to list files: {e}")
        raise HTTPException(status_code=500, detail="Failed to list files")

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    try:
        # MongoDB 연결 확인
        db_manager.mongo_client.admin.command('ping')
        
        # Elasticsearch 연결 확인
        db_manager.elasticsearch_client.ping()
        
        return {"status": "healthy", "message": "All services are running"}
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "message": str(e)}
        )

@app.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """파일 삭제"""
    try:
        # MongoDB에서 파일 메타데이터 조회
        file_data = db_manager.get_file_by_id(file_id)
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found")
        
        # 파일 시스템에서 실제 파일 삭제
        saved_filepath = file_data.get("saved_filepath")
        if saved_filepath and os.path.exists(saved_filepath):
            cleanup_file(saved_filepath)
        
        # MongoDB에서 메타데이터 삭제
        db_manager.mongo_collection.delete_one({"file_id": file_id})
        
        # Elasticsearch에서 벡터 삭제
        try:
            db_manager.elasticsearch_client.delete(
                index=Config.ELASTICSEARCH_INDEX,
                id=file_id
            )
        except Exception as e:
            logger.warning(f"Failed to delete vector from Elasticsearch: {e}")
        
        logger.info(f"File deleted successfully: {file_id}")
        
        return {
            "message": "File deleted successfully",
            "file_id": file_id,
            "filename": file_data.get("original_filename")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete file")

@app.get("/files/{file_id}/preview")
async def get_file_preview(file_id: str, size: int = Query(80, ge=50, le=300, description="썸네일 크기")):
    """파일 미리보기 (이미지 썸네일)"""
    try:
        # MongoDB에서 파일 메타데이터 조회
        file_data = db_manager.get_file_by_id(file_id)
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found")
        
        # 이미지 파일이 아닌 경우 오류
        if file_data["file_type"] != "image":
            raise HTTPException(status_code=400, detail="Preview only available for image files")
        
        # 파일 경로 확인
        saved_filepath = file_data.get("saved_filepath")
        if not saved_filepath or not os.path.exists(saved_filepath):
            raise HTTPException(status_code=404, detail="Image file not found")
        
        # 이미지 썸네일 생성
        try:
            with Image.open(saved_filepath) as img:
                # RGB로 변환
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 썸네일 크기로 리사이즈
                img.thumbnail((size, size), Image.Resampling.LANCZOS)
                
                # 바이트 스트림으로 변환
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG', quality=85)
                img_byte_arr.seek(0)
                
                def generate_image():
                    yield img_byte_arr.getvalue()
                
                return StreamingResponse(
                    generate_image(),
                    media_type="image/jpeg",
                    headers={"Cache-Control": "public, max-age=3600"}
                )
                
        except Exception as e:
            logger.error(f"Failed to generate thumbnail for {file_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate thumbnail")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get file preview {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get file preview")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 