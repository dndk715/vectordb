from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class FileType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"

class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    file_type: FileType
    file_size: int
    upload_time: datetime
    message: str

class SearchRequest(BaseModel):
    query: str
    file_type: Optional[FileType] = None
    limit: int = 10
    min_score: float = 0.1

class SearchResult(BaseModel):
    file_id: str
    filename: str
    file_type: FileType
    score: float
    metadata: Dict[str, Any]

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    query: str

class FileInfo(BaseModel):
    file_id: str
    filename: str
    file_type: FileType
    file_size: int
    upload_time: datetime
    metadata: Dict[str, Any]

class FileListResponse(BaseModel):
    files: List[FileInfo]
    total: int 