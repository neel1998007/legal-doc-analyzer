from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class DocumentCreate(BaseModel):
    """Schema for document upload"""
    original_filename: str
    file_type: str

class DocumentResponse(BaseModel):
    """Schema for document data in responses"""
    id: uuid.UUID
    user_id: uuid.UUID
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    processed: bool
    created_at: datetime

    model_config = {"from_attributes": True}

class DocumentListResponse(BaseModel):
    """Schema for list of documents"""
    documents: list[DocumentResponse]
    total: int