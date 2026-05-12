import os
import uuid
import shutil
from datetime import datetime
from typing import Optional, List
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.models.user import User

class DocumentService:
    """Service for handling document operations"""
    
    ALLOWED_EXTENSIONS = {'.pdf', '.docx'}
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    
    @staticmethod
    def validate_file(file: UploadFile) -> None:
        """Validate uploaded file"""
        
        # Check if file has content
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Check file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in DocumentService.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file_ext} not allowed. Allowed types: PDF, DOCX"
            )
        
        # Check MIME type
        if file.content_type not in DocumentService.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Expected PDF or DOCX"
            )
    
    @staticmethod
    async def save_file(file: UploadFile, user_id: uuid.UUID) -> tuple[str, str, int]:
        """
        Save uploaded file to disk
        Returns: (filename, file_path, file_size)
        """
        
        # Generate unique filename
        file_ext = os.path.splitext(file.filename)[1].lower()
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        
        # Create user-specific subdirectory
        user_upload_dir = os.path.join(settings.UPLOAD_DIRECTORY, str(user_id))
        os.makedirs(user_upload_dir, exist_ok=True)
        
        # Full file path
        file_path = os.path.join(user_upload_dir, unique_filename)
        
        # Save file
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Check file size
            if file_size > settings.MAX_FILE_SIZE:
                os.remove(file_path)  # Delete the file
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
                )
            
            return unique_filename, file_path, file_size
            
        except Exception as e:
            # Clean up if something goes wrong
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving file: {str(e)}"
            )
    
    @staticmethod
    async def create_document(
        db: Session,
        user_id: uuid.UUID,
        file: UploadFile
    ) -> Document:
        """Create a new document record"""
        
        # Validate file
        DocumentService.validate_file(file)
        
        # Save file to disk
        filename, file_path, file_size = await DocumentService.save_file(file, user_id)
        
        # Create database record
        document = Document(
            user_id=user_id,
            filename=filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file.content_type,
            processed=False
        )
        
        try:
            db.add(document)
            db.commit()
            db.refresh(document)
            return document
        except Exception as e:
            # Rollback database and delete file if DB insert fails
            db.rollback()
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating document record: {str(e)}"
            )
    
    @staticmethod
    def get_user_documents(
        db: Session,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """Get all documents for a user"""
        return db.query(Document)\
            .filter(Document.user_id == user_id)\
            .order_by(Document.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    @staticmethod
    def get_document_by_id(
        db: Session,
        document_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Optional[Document]:
        """Get a specific document by ID"""
        return db.query(Document)\
            .filter(
                Document.id == document_id,
                Document.user_id == user_id
            )\
            .first()
    
    @staticmethod
    def delete_document(
        db: Session,
        document_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> bool:
        """Delete a document"""
        document = DocumentService.get_document_by_id(db, document_id, user_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Delete file from disk
        try:
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")
        
        # Delete from database
        try:
            db.delete(document)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting document: {str(e)}"
            )