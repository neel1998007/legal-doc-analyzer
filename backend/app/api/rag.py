from urllib.parse import urlparse

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse
from app.services.chromadb_service import ChromaDBService
from app.services.rag_service import RAGService

router = APIRouter(prefix="/rag", tags=["RAG"])


def _chroma_host_port():
    parsed = urlparse(settings.CHROMADB_URL)
    host = parsed.hostname or "localhost"
    port = parsed.port or 8000
    return host, port


@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(
    payload: RAGQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    host, port = _chroma_host_port()
    rag = RAGService(chromadb_host=host, chromadb_port=port)

    collection_name = ChromaDBService.user_collection_name(str(current_user.id))
    doc_filter = str(payload.document_id) if payload.document_id else None

    results = rag.query_documents(
        query=payload.query,
        collection_name=collection_name,
        n_results=payload.top_k,
        document_id=doc_filter,
    )
    return results