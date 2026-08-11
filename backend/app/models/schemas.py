"""
Pydantic 数据模型
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID


class SessionCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    user_id: Optional[UUID] = None


class SessionUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class SessionResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID]
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    """
    创建消息的数据模型
    
    注意：session_id 会从路径参数中获取，不需要在请求体中提供
    """
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str
    tokens_used: Optional[int] = 0


class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    created_at: datetime
    tokens_used: int


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    collection_name: Optional[str] = Field(None, max_length=100)


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class KnowledgeBaseResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    collection_name: str
    user_id: Optional[UUID]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    document_count: int = 0
    
    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: UUID
    kb_id: UUID
    filename: str
    file_type: Optional[str]
    file_size: int
    chunk_count: int
    is_indexed: bool
    indexing_error: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5
    score_threshold: Optional[float] = 0.5


class SearchResult(BaseModel):
    content: str
    score: float
    metadata: dict
    
    class Config:
        from_attributes = True


class FileUploadResponse(BaseModel):
    id: UUID
    session_id: UUID
    filename: str
    file_size: int
    content_type: Optional[str]
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    status: str
    version: str
    services: dict


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None