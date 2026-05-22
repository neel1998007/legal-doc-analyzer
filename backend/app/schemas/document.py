from pydantic import BaseModel
from datetime import datetime
import uuid
from typing import Optional


class DocumentCreate(BaseModel):
    original_filename: str
    file_type: str


class DocumentResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    processed: bool
    created_at: datetime

    # New fields for async processing visibility
    processing_status: str
    processing_error: Optional[str] = None
    processed_at: Optional[datetime] = None
    processing_job_id: Optional[str] = None

    model_config = {"from_attributes": True}