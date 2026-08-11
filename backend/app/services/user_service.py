"""
用户服务层

处理用户注册、登录、认证等业务逻辑。
"""
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging
import uuid

from app.models.tables import User
from app.utils.auth import hash_password, verify_password, create_access_token, decode_access_token

logger = logging.getLogger(__name__)


class UserService:
    """用户服务类"""
    
    @staticmethod
    def register(
        db: Session,
        username: str,
        password: str,
        email: Optional[str] = None,
        nickname: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        用户注册
        
        Args:
            db: 数据库会话
            username: 用户名
            password: 密码
            email: 邮箱（可选）
            nickname: 昵称（可选）
        
        Returns:
            注册结果，包含用户信息和 token
        """
        # 检查用户名是否已存在
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            return {
                "success": False,
                "error": "用户名已存在"
            }
        
        # 检查邮箱是否已存在
        if email:
            existing_email = db.query(User).filter(User.email == email).first()
            if existing_email:
                return {
                    "success": False,
                    "error": "邮箱已被使用"
                }
        
        # 创建新用户
        password_hash = hash_password(password)
        
        new_user = User(
            username=username,
            password_hash=password_hash,
            email=email,
            nickname=nickname or username
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # 生成 token
        token = create_access_token({"sub": str(new_user.id), "username": new_user.username})
        
        logger.info(f"User registered: {username}")
        
        return {
            "success": True,
            "user": new_user.to_dict(),
            "token": token
        }
    
    @staticmethod
    def login(db: Session, username: str, password: str) -> Dict[str, Any]:
        """
        用户登录
        
        Args:
            db: 数据库会话
            username: 用户名
            password: 密码
        
        Returns:
            登录结果，包含用户信息和 token
        """
        # 查找用户
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            return {
                "success": False,
                "error": "用户名或密码错误"
            }
        
        # 验证密码
        if not verify_password(password, user.password_hash):
            return {
                "success": False,
                "error": "用户名或密码错误"
            }
        
        # 检查用户是否激活
        if not user.is_active:
            return {
                "success": False,
                "error": "用户已被禁用"
            }
        
        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        # 生成 token
        token = create_access_token({"sub": str(user.id), "username": user.username})
        
        logger.info(f"User logged in: {username}")
        
        return {
            "success": True,
            "user": user.to_dict(),
            "token": token
        }
    
    @staticmethod
    def get_current_user(db: Session, token: str) -> Optional[User]:
        """
        获取当前用户
        
        Args:
            db: 数据库会话
            token: JWT token
        
        Returns:
            用户对象，如果验证失败返回 None
        """
        payload = decode_access_token(token)
        
        if not payload:
            return None
        
        user_id = payload.get("sub")
        
        if not user_id:
            return None
        
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            return None
        
        user = db.query(User).filter(User.id == user_uuid).first()
        
        return user
    
    @staticmethod
    def logout(db: Session, user_id: str) -> Dict[str, Any]:
        """
        用户登出
        
        Args:
            db: 数据库会话
            user_id: 用户ID
        
        Returns:
            登出结果
        """
        logger.info(f"User logged out: {user_id}")
        
        return {
            "success": True,
            "message": "登出成功"
        }