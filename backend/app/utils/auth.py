"""
用户认证工具模块

提供密码哈希、JWT token 生成和验证等功能。
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import bcrypt
from jose import JWTError, jwt
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def hash_password(password: str) -> str:
    """
    对密码进行哈希
    
    Args:
        password: 原始密码
    
    Returns:
        哈希后的密码
    """
    # bcrypt 限制密码长度为 72 字节
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        import hashlib
        password_bytes = hashlib.sha256(password_bytes).hexdigest().encode('utf-8')
    
    # 生成盐并哈希密码
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Args:
        plain_password: 原始密码
        hashed_password: 哈希后的密码
    
    Returns:
        是否匹配
    """
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        import hashlib
        password_bytes = hashlib.sha256(password_bytes).hexdigest().encode('utf-8')
    
    return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT access token
    
    Args:
        data: 要编码的数据（通常是用户ID等）
        expires_delta: 过期时间增量
    
    Returns:
        JWT token 字符串
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码 JWT access token
    
    Args:
        token: JWT token 字符串
    
    Returns:
        解码后的数据，如果验证失败返回 None
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        return None