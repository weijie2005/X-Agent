"""
PDF 导出 API 路由
"""
import logging
import os
import tempfile
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import asyncio

from app.services.pdf_exporter import PDFExporter
from app.agent.memory.memory_system import MemorySystem

logger = logging.getLogger(__name__)

router = APIRouter()


class ExportPDFRequest(BaseModel):
    """PDF 导出请求"""
    session_id: str


class ExportPDFResponse(BaseModel):
    """PDF 导出响应"""
    success: bool
    message: str
    file_path: str = None


# 全局 PDF 导出器
pdf_exporter = PDFExporter()


@router.post("/export-pdf")
async def export_pdf(request: ExportPDFRequest):
    """
    导出聊天记录到 PDF
    
    Args:
        request: 导出请求
    
    Returns:
        PDF 文件流
    """
    try:
        logger.info(f"Exporting PDF for session: {request.session_id}")
        
        # 获取会话记录
        memory_system = MemorySystem()
        session_data = await memory_system.get_session(request.session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        messages = session_data.get("messages", [])
        
        if not messages:
            raise HTTPException(status_code=400, detail="No messages to export")
        
        # 生成临时文件路径
        output_path = os.path.join(
            tempfile.gettempdir(),
            f"chat_{request.session_id}.pdf"
        )
        
        # 导出 PDF
        await pdf_exporter.export_chat_to_pdf(
            messages=messages,
            session_id=request.session_id,
            output_path=output_path
        )
        
        # 返回文件
        return FileResponse(
            path=output_path,
            media_type="application/pdf",
            filename=f"chat_{request.session_id}.pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.on_event("shutdown")
async def shutdown_event():
    """
    应用关闭时清理资源
    """
    await pdf_exporter.close()