"""
文件上传相关接口
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.models.database import get_db
from app.models.schemas import FileUploadResponse, ErrorResponse
from app.services.file_service import FileService
from app.config import get_settings

router = APIRouter(prefix="/files", tags=["files"])
settings = get_settings()


@router.post(
    "/upload/{session_id}",
    response_model=FileUploadResponse,
    status_code=201,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse}
    }
)
async def upload_file(
    session_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    上传文件到指定会话
    
    - 文件大小限制：50MB
    - 支持格式：PDF, DOCX, DOC, XLSX, XLS, TXT, MD
    """
    file_size = 0
    content = await file.read()
    file_size = len(content)
    
    if file_size > settings.FILE_MAX_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum limit of {settings.FILE_MAX_SIZE / (1024*1024)}MB"
        )
    
    file_ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if file_ext not in settings.FILE_ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.FILE_ALLOWED_EXTENSIONS)}"
        )
    
    try:
        service = FileService(db)
        
        from io import BytesIO
        file_data = BytesIO(content)
        
        file_metadata = service.upload_file(
            session_id=session_id,
            file_data=file_data,
            filename=file.filename,
            content_type=file.content_type
        )
        
        return file_metadata
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@router.get("/{file_id}", response_model=FileUploadResponse)
async def get_file_metadata(
    file_id: UUID,
    db: Session = Depends(get_db)
):
    """
    获取文件元数据
    """
    service = FileService(db)
    file_metadata = service.get_file(file_id)
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    return file_metadata


@router.get("/session/{session_id}", response_model=List[FileUploadResponse])
async def get_session_files(
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """
    获取会话的所有文件
    """
    service = FileService(db)
    files = service.get_session_files(session_id)
    return files


@router.get("/{file_id}/url")
async def get_file_url(
    file_id: UUID,
    expires: int = Query(3600, ge=60, le=86400, description="URL有效期（秒）"),
    db: Session = Depends(get_db)
):
    """
    获取文件临时访问URL
    """
    service = FileService(db)
    url = service.get_file_url(file_id, expires=expires)
    if not url:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {"url": url, "expires_in": expires}


@router.delete("/{file_id}", status_code=204)
async def delete_file(
    file_id: UUID,
    db: Session = Depends(get_db)
):
    """
    删除文件
    """
    service = FileService(db)
    success = service.delete_file(file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")