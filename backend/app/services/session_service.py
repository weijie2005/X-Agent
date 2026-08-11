"""
会话服务层
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import logging

from app.models.tables import Session as SessionModel, Message, MessageRole
from app.models.schemas import SessionCreate, SessionUpdate, MessageCreate

logger = logging.getLogger(__name__)


class SessionService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_session(self, session_data: SessionCreate) -> SessionModel:
        """
        创建新会话
        
        Args:
            session_data: 会话创建数据
        
        Returns:
            SessionModel: 创建的会话对象
        """
        session = SessionModel(
            user_id=session_data.user_id,
            title=session_data.title or f"会话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        logger.info(f"Created session: {session.id}")
        return session
    
    def get_session(self, session_id: UUID) -> Optional[SessionModel]:
        """
        获取会话详情
        
        Args:
            session_id: 会话ID
        
        Returns:
            SessionModel: 会话对象
        """
        return self.db.query(SessionModel).filter(
            and_(
                SessionModel.id == session_id,
                SessionModel.is_active == True
            )
        ).first()
    
    def list_sessions(
        self,
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[SessionModel]:
        """
        获取会话列表
        
        Args:
            user_id: 用户ID（可选）
            skip: 跳过数量
            limit: 限制数量
        
        Returns:
            List[SessionModel]: 会话列表
        """
        query = self.db.query(SessionModel).filter(SessionModel.is_active == True)
        
        if user_id:
            query = query.filter(SessionModel.user_id == user_id)
        
        return query.order_by(SessionModel.updated_at.desc()).offset(skip).limit(limit).all()
    
    def update_session(
        self,
        session_id: UUID,
        session_data: SessionUpdate
    ) -> Optional[SessionModel]:
        """
        更新会话
        
        Args:
            session_id: 会话ID
            session_data: 更新数据
        
        Returns:
            SessionModel: 更新后的会话对象
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        if session_data.title is not None:
            session.title = session_data.title
        if session_data.is_active is not None:
            session.is_active = session_data.is_active
        
        self.db.commit()
        self.db.refresh(session)
        
        logger.info(f"Updated session: {session_id}")
        return session
    
    def delete_session(self, session_id: UUID) -> bool:
        """
        删除会话（软删除）
        
        Args:
            session_id: 会话ID
        
        Returns:
            bool: 删除是否成功
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.is_active = False
        self.db.commit()
        
        logger.info(f"Deleted session: {session_id}")
        return True
    
    def add_message(self, session_id: UUID, message_data: MessageCreate) -> Message:
        """
        添加消息到会话
        
        Args:
            session_id: 会话 ID
            message_data: 消息数据
        
        Returns:
            Message: 创建的消息对象
        """
        message = Message(
            session_id=session_id,
            role=MessageRole(message_data.role),
            content=message_data.content,
            tokens_used=message_data.tokens_used or 0
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        logger.info(f"Added message to session {message.session_id}")
        return message
    
    def get_messages(
        self,
        session_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Message]:
        """
        获取会话历史消息
        
        Args:
            session_id: 会话ID
            skip: 跳过数量
            limit: 限制数量
        
        Returns:
            List[Message]: 消息列表
        """
        return self.db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.created_at.asc()).offset(skip).limit(limit).all()