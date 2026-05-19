from typing import List
from urllib.parse import urlparse
import uuid

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.api.auth import get_current_user
from app.models.user import User
from app.models.document import Document
from app.schemas.document import DocumentResponse
from app.schemas.rag import ProcessDocumentResponse
from app.services.document_service import DocumentService
from app.services.rag_service import RAGService
from app.services.chromadb_service import ChromaDBService
from rq import Queue
from app.core.redis_client import get_redis_connection
from app.tasks.document_tasks import process_document_task

router = APIRouter(prefix="/documents", tags=["Documents"])


def _chroma_host_port():
    parsed = urlparse(settings.CHROMADB_URL)
    host = parsed.hostname or "localhost"
    port = parsed.port or 8000
    return host, port


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = await DocumentService.create_document(
        db=db,
        user_id=current_user.id,
        file=file,
    )
    return document


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    documents = DocumentService.get_user_documents(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = DocumentService.get_document_by_id(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.post("/{document_id}/process", response_model=ProcessDocumentResponse)
async def process_document(
    document_id: uuid.UUID,
    force: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Process a document into chunks+embeddings and store in ChromaDB.
    Uses collection-per-user.
    """
    document = DocumentService.get_document_by_id(db, document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.processed and not force:
        return {
            "document_id": str(document.id),
            "success": True,
            "steps": {},
            "error": None,
        }

    host, port = _chroma_host_port()

    # user-specific collection
    collection_name = ChromaDBService.user_collection_name(str(current_user.id))

    # If reprocessing, delete old vectors for this document first
    if force:
        try:
            chroma = ChromaDBService(host=host, port=port)
            chroma.create_collection(collection_name)  # ensure exists
            chroma.delete_where(collection_name, where={"document_id": str(document.id)})
        except Exception:
            # ignore if collection doesn't exist yet
            pass

    rag = RAGService(
        chromadb_host=host,
        chromadb_port=port,
        chunk_size=500,
        chunk_overlap=50,
        min_chunk_size=100,
    )

    result = rag.process_document(
        file_path=document.file_path,
        file_type=document.file_type,
        document_id=str(document.id),
        collection_name=collection_name,
        metadata={
            "user_id": str(current_user.id),
            "original_filename": document.original_filename,
        },
    )

    if result.get("success"):
        document.processed = True
        db.commit()

    return result


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Delete vectors (best-effort)
    try:
        host, port = _chroma_host_port()
        chroma = ChromaDBService(host=host, port=port)
        collection_name = ChromaDBService.user_collection_name(str(current_user.id))
        chroma.delete_where(collection_name, where={"document_id": str(document_id)})
    except Exception:
        pass

    DocumentService.delete_document(db=db, document_id=document_id, user_id=current_user.id)
    return None


@router.get("/stats/summary")
async def get_document_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    documents = DocumentService.get_user_documents(db, current_user.id)

    total_size = sum(doc.file_size for doc in documents)
    processed_count = sum(1 for doc in documents if doc.processed)

    return {
        "total_documents": len(documents),
        "processed_documents": processed_count,
        "pending_documents": len(documents) - processed_count,
        "total_storage_bytes": total_size,
        "total_storage_mb": round(total_size / 1024 / 1024, 2),
    }

@router.post("/{document_id}/process-async")
async def process_document_async(
    document_id: uuid.UUID,
    force: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = DocumentService.get_document_by_id(db, document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    redis_conn = get_redis_connection()
    queue = Queue("document_processing", connection=redis_conn)

    job = queue.enqueue(
        process_document_task,
        str(document_id),
        str(current_user.id),
        force=force,
        job_timeout=900,  # 15 minutes
    )
    job.meta["user_id"] = str(current_user.id)
    job.meta["document_id"] = str(document_id)
    job.save_meta()

    # Update DB status immediately
    document.processing_status = "queued"
    document.processing_error = None
    db.commit()

    return {
        "job_id": job.id,
        "status": job.get_status(),
        "document_id": str(document_id),
    }