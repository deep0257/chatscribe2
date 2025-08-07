from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user_from_token
from app.models.models import User
from app.schemas.schemas import Document, DocumentCreate
from app.crud.crud import create_document, get_user_documents, get_document
from app.core.file_processor import file_processor
from app.core.alternative_ai_service import alternative_ai_service as ai_service
from app.core.config import settings

router = APIRouter()


@router.post("/upload", response_model=Document)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Upload and process a document"""
    
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    if not file_processor.is_allowed_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size
    file_content = await file.read()
    if len(file_content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024):.1f} MB"
        )
    
    # Process file
    file_path, unique_filename, extracted_text = file_processor.process_uploaded_file(
        file_content, file.filename
    )
    
    if not file_path or not extracted_text:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process file"
        )
    
    # Create document record
    document_create = DocumentCreate(
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_type=file.filename.split('.')[-1].lower(),
        file_size=len(file_content),
        content=extracted_text
    )
    
    document = create_document(db, document_create, current_user.id)
    
    # Process document for AI (asynchronously in background)
    try:
        ai_service.process_document_content(extracted_text, document.id)
    except Exception as e:
        print(f"Error processing document for AI: {e}")
        # Don't fail the upload if AI processing fails
    
    return document


@router.get("/", response_model=List[Document])
def get_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Get user's documents"""
    return get_user_documents(db, current_user.id)


@router.get("/{document_id}", response_model=Document)
def get_document_detail(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Get specific document details"""
    document = get_document(db, document_id, current_user.id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return document


@router.post("/{document_id}/summarize")
def summarize_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Generate document summary"""
    document = get_document(db, document_id, current_user.id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if not document.content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document content not available"
        )
    
    try:
        summary = ai_service.summarize_document(document.content)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate summary"
        )
