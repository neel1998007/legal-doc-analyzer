from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.schemas.document import DocumentResponse, DocumentListResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a legal document (PDF or DOCX)
    """
    document = await DocumentService.create_document(
        db=db,
        user_id=current_user.id,
        file=file
    )
    return document

@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all documents for the current user
    """
    documents = DocumentService.get_user_documents(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return documents

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific document by ID
    """
    document = DocumentService.get_document_by_id(
        db=db,
        document_id=document_id,
        user_id=current_user.id
    )
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return document

@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a document
    """
    DocumentService.delete_document(
        db=db,
        document_id=document_id,
        user_id=current_user.id
    )
    return None

@router.get("/stats/summary")
async def get_document_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get document statistics for current user
    """
    documents = DocumentService.get_user_documents(db, current_user.id)
    
    total_size = sum(doc.file_size for doc in documents)
    processed_count = sum(1 for doc in documents if doc.processed)
    
    return {
        "total_documents": len(documents),
        "processed_documents": processed_count,
        "pending_documents": len(documents) - processed_count,
        "total_storage_bytes": total_size,
        "total_storage_mb": round(total_size / 1024 / 1024, 2)
    }