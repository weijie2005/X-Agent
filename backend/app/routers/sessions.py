"""
会话相关接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.models.database import get_db
from app.models.schemas import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    MessageCreate,
    MessageResponse
)
from app.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db)
):
    """
    创建新会话
    """
    service = SessionService(db)
    session = service.create_session(session_data)
    return session


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    user_id: Optional[UUID] = Query(None, description="用户ID"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="限制数量"),
    db: Session = Depends(get_db)
):
    """
    获取会话列表
    """
    service = SessionService(db)
    sessions = service.list_sessions(user_id=user_id, skip=skip, limit=limit)
    return sessions


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """
    获取会话详情
    """
    service = SessionService(db)
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: UUID,
    session_data: SessionUpdate,
    db: Session = Depends(get_db)
):
    """
    更新会话
    """
    service = SessionService(db)
    session = service.update_session(session_id, session_data)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """
    删除会话（软删除）
    """
    service = SessionService(db)
    success = service.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("/{session_id}/messages", response_model=MessageResponse, status_code=201)
async def add_message(
    session_id: UUID,
    message_data: MessageCreate,
    db: Session = Depends(get_db)
):
    """
    添加消息到会话
    
    Args:
        session_id: 会话 ID（路径参数）
        message_data: 消息数据（请求体）
    
    Returns:
        MessageResponse: 创建的消息对象
    """
    service = SessionService(db)
    message = service.add_message(session_id, message_data)
    return message


@router.get("/{session_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    session_id: UUID,
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=500, description="限制数量"),
    db: Session = Depends(get_db)
):
    """
    获取会话历史消息
    """
    service = SessionService(db)
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = service.get_messages(session_id, skip=skip, limit=limit)
    return messages