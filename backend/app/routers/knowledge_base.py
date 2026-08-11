"""
知识库管理接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.models.database import get_db
from app.models.schemas import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    DocumentResponse,
    SearchRequest,
    SearchResult
)
from app.services.knowledge_base_service import KnowledgeBaseService
from app.agent.rag.agentic_rag import AgenticRAG

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])


@router.post("", response_model=KnowledgeBaseResponse, status_code=201)
async def create_knowledge_base(
    kb_data: KnowledgeBaseCreate,
    user_id: Optional[UUID] = Query(None, description="用户ID"),
    db: Session = Depends(get_db)
):
    """
    创建知识库
    """
    service = KnowledgeBaseService(db)
    kb = service.create_knowledge_base(kb_data, user_id)
    return kb


@router.get("", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_bases(
    user_id: Optional[UUID] = Query(None, description="用户ID"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="限制数量"),
    db: Session = Depends(get_db)
):
    """
    获取知识库列表
    """
    service = KnowledgeBaseService(db)
    kbs = service.list_knowledge_bases(user_id=user_id, skip=skip, limit=limit)
    return kbs


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: UUID,
    db: Session = Depends(get_db)
):
    """
    获取知识库详情
    """
    service = KnowledgeBaseService(db)
    kb = service.get_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb


@router.patch("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: UUID,
    kb_data: KnowledgeBaseUpdate,
    db: Session = Depends(get_db)
):
    """
    更新知识库
    """
    service = KnowledgeBaseService(db)
    kb = service.update_knowledge_base(kb_id, kb_data)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb


@router.delete("/{kb_id}", status_code=204)
async def delete_knowledge_base(
    kb_id: UUID,
    db: Session = Depends(get_db)
):
    """
    删除知识库（软删除）
    """
    service = KnowledgeBaseService(db)
    success = service.delete_knowledge_base(kb_id)
    if not success:
        raise HTTPException(status_code=404, detail="Knowledge base not found")


@router.post("/{kb_id}/documents", response_model=DocumentResponse, status_code=201)
async def upload_document(
    kb_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    上传文档到知识库
    """
    service = KnowledgeBaseService(db)
    
    # 读取文件内容
    file_content = await file.read()
    
    # 获取文件类型
    file_type = file.filename.split('.')[-1] if '.' in file.filename else 'txt'
    
    try:
        document = await service.upload_document(
            kb_id=kb_id,
            file_content=file_content,
            filename=file.filename,
            file_type=file_type
        )
        return document
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")


@router.get("/{kb_id}/documents", response_model=List[DocumentResponse])
async def list_documents(
    kb_id: UUID,
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="限制数量"),
    db: Session = Depends(get_db)
):
    """
    获取知识库文档列表
    """
    service = KnowledgeBaseService(db)
    
    # 检查知识库是否存在
    kb = service.get_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    documents = service.list_documents(kb_id=kb_id, skip=skip, limit=limit)
    return documents


@router.delete("/{kb_id}/documents/{document_id}", status_code=204)
async def delete_document(
    kb_id: UUID,
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """
    删除文档
    """
    service = KnowledgeBaseService(db)
    success = service.delete_document(kb_id=kb_id, document_id=document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")


@router.post("/{kb_id}/search", response_model=List[SearchResult])
async def search_knowledge_base(
    kb_id: UUID,
    search_request: SearchRequest,
    db: Session = Depends(get_db)
):
    """
    检索知识库
    """
    service = KnowledgeBaseService(db)
    
    # 检查知识库是否存在
    kb = service.get_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    try:
        # 使用Agentic RAG检索
        rag = AgenticRAG(collection_name=kb.collection_name)
        retrieval_result = rag.retrieve(search_request.query)
        
        # 格式化结果
        results = []
        for result in retrieval_result.get('results', []):
            results.append(SearchResult(
                content=result.get('content', ''),
                score=result.get('combined_score', result.get('score', 0)),
                metadata=result.get('metadata', {})
            ))
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")