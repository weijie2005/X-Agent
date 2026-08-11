"""
SSE 流式响应工具
"""
from fastapi import Response
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)


class SSEResponse(StreamingResponse):
    """
    SSE 流式响应类
    """
    media_type = "text/event-stream"
    
    def __init__(
        self,
        content: AsyncGenerator[str, None],
        status_code: int = 200,
        headers: Optional[dict] = None
    ):
        default_headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
        if headers:
            default_headers.update(headers)
        
        super().__init__(
            content=content,
            status_code=status_code,
            headers=default_headers,
            media_type=self.media_type
        )


async def format_sse_message(data: Any, event: Optional[str] = None) -> str:
    """
    格式化 SSE 消息
    
    Args:
        data: 消息数据
        event: 事件类型（可选）
    
    Returns:
        str: 格式化后的 SSE 消息
    """
    if isinstance(data, str):
        message = data
    else:
        message = json.dumps(data, ensure_ascii=False)
    
    if event:
        return f"event: {event}\ndata: {message}\n\n"
    else:
        return f"data: {message}\n\n"


async def create_sse_stream(
    generator: AsyncGenerator[Any, None],
    event_name: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    创建 SSE 流式响应生成器
    
    Args:
        generator: 异步生成器
        event_name: 事件名称（可选）
    
    Yields:
        str: 格式化后的 SSE 消息
    """
    try:
        async for chunk in generator:
            yield await format_sse_message(chunk, event_name)
    except Exception as e:
        logger.error(f"SSE stream error: {e}")
        error_data = {"error": str(e)}
        yield await format_sse_message(error_data, "error")
    finally:
        yield await format_sse_message("[DONE]", "done")


class SSEStreamer:
    """
    SSE 流式响应辅助类
    """
    
    @staticmethod
    async def stream_text(text_generator: AsyncGenerator[str, None]):
        """
        流式输出文本（打字机效果）
        
        Args:
            text_generator: 文本异步生成器
        
        Yields:
            str: SSE 格式的消息
        """
        async for chunk in text_generator:
            yield await format_sse_message({"text": chunk}, "message")
        
        yield await format_sse_message("[DONE]", "done")
    
    @staticmethod
    async def stream_json(data_generator: AsyncGenerator[dict, None]):
        """
        流式输出 JSON 数据
        
        Args:
            data_generator: JSON 数据异步生成器
        
        Yields:
            str: SSE 格式的消息
        """
        async for data in data_generator:
            yield await format_sse_message(data, "data")
        
        yield await format_sse_message("[DONE]", "done")
    
    @staticmethod
    async def stream_progress(
        total: int,
        current: int,
        message: str = ""
    ):
        """
        流式输出进度信息
        
        Args:
            total: 总数
            current: 当前进度
            message: 进度消息
        
        Yields:
            str: SSE 格式的消息
        """
        progress_data = {
            "total": total,
            "current": current,
            "percentage": round(current / total * 100, 2) if total > 0 else 0,
            "message": message
        }
        yield await format_sse_message(progress_data, "progress")