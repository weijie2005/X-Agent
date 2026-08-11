"""
用户认证接口

提供用户注册、登录、登出等功能。
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging

from app.models.database import get_db
from app.services.user_service import UserService
from app.models.tables import User

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

logger = logging.getLogger(__name__)


class RegisterRequest(BaseModel):
    """注册请求模型"""
    username: str
    password: str
    email: Optional[EmailStr] = None
    nickname: Optional[str] = None


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str
    password: str


class UpdateProfileRequest(BaseModel):
    """更新个人信息请求模型"""
    nickname: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    department: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    old_password: str
    new_password: str


class UserResponse(BaseModel):
    """用户响应模型"""
    id: str
    username: str
    email: Optional[str]
    nickname: str
    phone: Optional[str]
    department: Optional[str]
    avatar_url: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str
    last_login_at: Optional[str]


class AuthResponse(BaseModel):
    """认证响应模型"""
    success: bool
    user: Optional[UserResponse] = None
    token: Optional[str] = None
    error: Optional[str] = None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前用户（依赖注入）
    
    用于需要认证的接口，自动验证 token 并返回用户对象。
    
    Raises:
        HTTPException: 如果 token 无效或用户不存在
    """
    token = credentials.credentials
    user = UserService.get_current_user(db, token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


@router.post("/register", response_model=AuthResponse)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    用户注册
    
    创建新用户账号，返回用户信息和 token。
    """
    logger.info(f"Register request for username: {request.username}")
    
    result = UserService.register(
        db=db,
        username=request.username,
        password=request.password,
        email=request.email,
        nickname=request.nickname
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return AuthResponse(**result)


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    用户登录
    
    验证用户名和密码，返回用户信息和 token。
    """
    logger.info(f"Login request for username: {request.username}")
    
    result = UserService.login(
        db=db,
        username=request.username,
        password=request.password
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["error"]
        )
    
    return AuthResponse(**result)


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    用户登出
    
    记录登出日志（客户端需要删除 token）。
    """
    result = UserService.logout(db, str(current_user.id))
    
    return result


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户信息
    
    返回当前登录用户的详细信息。
    """
    return UserResponse(**current_user.to_dict())


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新个人信息
    
    更新当前用户的昵称、邮箱、手机号和部门。
    """
    logger.info(f"Update profile request for user: {current_user.username}")
    
    # 更新用户信息
    if request.nickname is not None:
        current_user.nickname = request.nickname
    
    if request.email is not None:
        # 检查邮箱是否已被其他用户使用
        existing_user = db.query(User).filter(
            User.email == request.email,
            User.id != current_user.id
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被其他用户使用"
            )
        
        current_user.email = request.email
    
    if request.phone is not None:
        current_user.phone = request.phone
    
    if request.department is not None:
        current_user.department = request.department
    
    db.commit()
    db.refresh(current_user)
    
    logger.info(f"Profile updated successfully for user: {current_user.username}")
    
    return UserResponse(**current_user.to_dict())


@router.put("/password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改密码
    
    验证当前密码并更新为新密码。
    """
    logger.info(f"Change password request for user: {current_user.username}")
    
    from app.utils.auth import verify_password, hash_password
    
    # 验证当前密码
    if not verify_password(request.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误"
        )
    
    # 验证新密码长度
    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码长度至少为6位"
        )
    
    # 更新密码
    current_user.password_hash = hash_password(request.new_password)
    db.commit()
    
    logger.info(f"Password changed successfully for user: {current_user.username}")
    
    return {
        "success": True,
        "message": "密码修改成功"
    }