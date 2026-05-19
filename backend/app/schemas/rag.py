from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from uuid import UUID


class ProcessDocumentResponse(BaseModel):
    document_id: str
    success: bool
    steps: Dict[str, Any]
    error: Optional[str] = None


class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = 5
    document_id: Optional[UUID] = None


class RetrievedChunk(BaseModel):
    text: str
    metadata: Dict[str, Any]
    distance: float
    similarity: float


class RAGQueryResponse(BaseModel):
    query: str
    results: List[RetrievedChunk]