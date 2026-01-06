"""
Document Parser routes - PDF and DOCX to Markdown conversion
"""
import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status, UploadFile, File

from app.services.document_parser_service import document_parser_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/parse", tags=["Document Parser"])


@router.post("/pdf-to-markdown", response_model=Dict[str, Any])
async def parse_pdf_to_markdown(
    file: UploadFile = File(..., description="PDF file to convert to markdown")
):
    """
    Parse a PDF file and convert it to Markdown format for Quill editor
    
    Returns:
        - success: Whether parsing succeeded
        - markdown: The converted markdown content
        - filename: Original filename
        - pages: Number of pages in PDF
    """
    is_valid, error = document_parser_service.validate_file_extension(file.filename, 'pdf')
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    content = await file.read()
    result = await document_parser_service.parse_pdf(content, file.filename)
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse PDF: {result.error}"
        )
    
    return {
        "success": result.success,
        "markdown": result.markdown,
        "filename": result.filename,
        "pages": result.pages
    }


@router.post("/docx-to-markdown", response_model=Dict[str, Any])
async def parse_docx_to_markdown(
    file: UploadFile = File(..., description="DOCX file to convert to markdown")
):
    """
    Parse a DOCX file and convert it to Markdown format for Quill editor
    
    Returns:
        - success: Whether parsing succeeded
        - markdown: The converted markdown content
        - filename: Original filename
    """
    is_valid, error = document_parser_service.validate_file_extension(file.filename, 'docx')
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    content = await file.read()
    result = await document_parser_service.parse_docx(content, file.filename)
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse DOCX: {result.error}"
        )
    
    return {
        "success": result.success,
        "markdown": result.markdown,
        "filename": result.filename
    }
