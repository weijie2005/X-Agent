"""
PDF 导出接口

支持导出完整会话记录到 PDF，包括文本、表格、图表。
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

from app.services.pdf_exporter import PDFExporter
from app.agent.memory.memory_system import MemorySystem

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pdf", tags=["pdf"])


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


@router.post("/export")
async def export_session_pdf(request: ExportPDFRequest):
    """
    导出会话为 PDF
    
    功能：
    - 读取完整会话记录
    - 组装完整 HTML（含文本+表格+图表）
    - Playwright 无头浏览器渲染生成 PDF
    - 返回文件流前端下载
    
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
        
        # 导出 PDF
        import tempfile
        import os
        
        output_path = os.path.join(
            tempfile.gettempdir(),
            f"chat_{request.session_id}.pdf"
        )
        
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