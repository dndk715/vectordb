import os
import uuid
import mimetypes
from datetime import datetime
from typing import Tuple
import aiofiles
from fastapi import UploadFile
import logging

logger = logging.getLogger(__name__)

# 지원하는 파일 타입들
SUPPORTED_TEXT_EXTENSIONS = {'.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv'}
SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
SUPPORTED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv'}

def get_file_type(filename: str) -> str:
    """파일 확장자를 기반으로 파일 타입을 결정"""
    _, ext = os.path.splitext(filename.lower())
    
    if ext in SUPPORTED_TEXT_EXTENSIONS:
        return "text"
    elif ext in SUPPORTED_IMAGE_EXTENSIONS:
        return "image"
    elif ext in SUPPORTED_VIDEO_EXTENSIONS:
        return "video"
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def is_supported_file(filename: str) -> bool:
    """파일이 지원되는 타입인지 확인"""
    try:
        get_file_type(filename)
        return True
    except ValueError:
        return False

async def save_uploaded_file(upload_file: UploadFile, upload_dir: str) -> Tuple[str, int]:
    """업로드된 파일을 저장하고 파일 경로와 크기를 반환"""
    try:
        # 고유한 파일명 생성
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(upload_file.filename)[1]
        saved_filename = f"{file_id}{file_extension}"
        file_path = os.path.join(upload_dir, saved_filename)
        
        # 파일 저장
        async with aiofiles.open(file_path, 'wb') as f:
            content = await upload_file.read()
            await f.write(content)
        
        file_size = len(content)
        logger.info(f"File saved: {file_path}, size: {file_size} bytes")
        
        return file_path, file_size
        
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise

def create_file_metadata(
    file_id: str,
    original_filename: str,
    saved_filepath: str,
    file_type: str,
    file_size: int
) -> dict:
    """파일 메타데이터 생성"""
    return {
        "file_id": file_id,
        "original_filename": original_filename,
        "saved_filepath": saved_filepath,
        "file_type": file_type,
        "file_size": file_size,
        "upload_time": datetime.utcnow(),
        "mime_type": mimetypes.guess_type(original_filename)[0],
        "metadata": {
            "filename": original_filename,
            "file_type": file_type,
            "upload_time": datetime.utcnow().isoformat()
        }
    }

def format_file_size(size_bytes: int) -> str:
    """파일 크기를 사람이 읽기 쉬운 형태로 변환"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"

def validate_file_size(file_size: int, max_size_mb: int = 100) -> bool:
    """파일 크기 검증"""
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes

def cleanup_file(file_path: str):
    """파일 정리"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up file: {file_path}")
    except Exception as e:
        logger.error(f"Failed to cleanup file {file_path}: {e}")

def get_file_info(file_path: str) -> dict:
    """파일 정보 조회"""
    try:
        stat = os.stat(file_path)
        return {
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime),
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "exists": True
        }
    except FileNotFoundError:
        return {"exists": False}
    except Exception as e:
        logger.error(f"Failed to get file info for {file_path}: {e}")
        return {"exists": False, "error": str(e)} 