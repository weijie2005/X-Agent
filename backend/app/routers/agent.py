"""
Agent 对话接口

提供与 Agent 进行对话交互的 API 接口，支持：
- 同步对话（完整响应）
- 流式对话（SSE 实时推送）

日志记录：
- 所有对话请求和响应都会记录到 agent.log
- 包含会话ID、用户输入、响应内容、处理时间等
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel
import time
import json

from app.models.database import get_db
from app.services.agent_service import AgentService
from app.utils.sse import SSEResponse
from app.utils.logger import get_logger

router = APIRouter(prefix="/agent", tags=["agent"])

# 获取日志记录器
logger = get_logger(__name__, 'agent')


class ChatRequest(BaseModel):
    """对话请求模型"""
    session_id: UUID
    user_input: str
    user_id: Optional[UUID] = None
    knowledge_base_id: Optional[UUID] = None
    document_ids: Optional[List[UUID]] = None


class ChatResponse(BaseModel):
    """对话响应模型"""
    success: bool
    output: str
    metadata: dict


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    执行对话（同步）
    
    与 Agent 进行对话交互，返回完整响应。
    
    日志记录：
    - 请求开始：记录会话ID、用户输入
    - 请求完成：记录响应内容、处理时间
    - 请求失败：记录错误信息、堆栈
    """
    start_time = time.time()
    
    # 记录请求开始
    logger.info(
        f"Chat request started",
        extra={
            'session_id': str(request.session_id),
            'user_input': request.user_input[:100],  # 只记录前100个字符
            'user_id': str(request.user_id) if request.user_id else None
        }
    )
    
    try:
        service = AgentService()
        
        result = await service.chat(
            session_id=str(request.session_id),
            user_input=request.user_input,
            user_id=str(request.user_id) if request.user_id else None,
            knowledge_base_id=str(request.knowledge_base_id) if request.knowledge_base_id else None,
            document_ids=[str(doc_id) for doc_id in request.document_ids] if request.document_ids else None
        )
        
        process_time = time.time() - start_time
        
        # 记录请求完成
        logger.info(
            f"Chat request completed",
            extra={
                'session_id': str(request.session_id),
                'success': result.get('success', False),
                'output_length': len(result.get('output', '')),
                'process_time': process_time
            }
        )
        
        return ChatResponse(**result)
        
    except Exception as e:
        process_time = time.time() - start_time
        
        # 记录请求失败
        logger.error(
            f"Chat request failed: {str(e)}",
            extra={
                'session_id': str(request.session_id),
                'process_time': process_time
            },
            exc_info=True
        )
        raise


@router.post("/chat/stream")
async def stream_chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    执行对话（流式）
    
    与 Agent 进行对话交互，实时流式返回响应。
    支持 SSE（Server-Sent Events）协议。
    
    日志记录：
    - 请求开始：记录会话ID、用户输入
    - 流式完成：记录总处理时间
    - 请求失败：记录错误信息、堆栈
    """
    start_time = time.time()
    
    # 记录请求开始
    logger.info(
        f"Stream chat request started",
        extra={
            'session_id': str(request.session_id),
            'user_input': request.user_input[:100],  # 只记录前100个字符
            'user_id': str(request.user_id) if request.user_id else None
        }
    )
    
    try:
        service = AgentService()
        
        # 创建流式响应
        async def stream_with_logging():
            """流式响应生成器，添加日志记录"""
            try:
                async for chunk in service.stream_chat(
                    session_id=str(request.session_id),
                    user_input=request.user_input,
                    user_id=str(request.user_id) if request.user_id else None,
                    knowledge_base_id=str(request.knowledge_base_id) if request.knowledge_base_id else None,
                    document_ids=[str(doc_id) for doc_id in request.document_ids] if request.document_ids else None
                ):
                    yield chunk
            finally:
                # 记录流式完成
                process_time = time.time() - start_time
                logger.info(
                    f"Stream chat request completed",
                    extra={
                        'session_id': str(request.session_id),
                        'process_time': process_time
                    }
                )
        
        return SSEResponse(content=stream_with_logging())
        
    except Exception as e:
        process_time = time.time() - start_time
        
        # 记录请求失败
        logger.error(
            f"Stream chat request failed: {str(e)}",
            extra={
                'session_id': str(request.session_id),
                'process_time': process_time
            },
            exc_info=True
        )
        raise