from datetime import datetime
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.document import Document
from app.services.chromadb_service import ChromaDBService
from app.services.rag_service import RAGService


def _chroma_host_port():
    parsed = urlparse(settings.CHROMADB_URL)
    host = parsed.hostname or "localhost"
    port = parsed.port or 8000
    return host, port


def process_document_task(document_id: str, user_id: str, force: bool = False) -> dict:
    """
    Background job:
    - Marks doc as processing
    - Runs extract->chunk->embed->store
    - Marks processed/failed
    """
    db: Session = SessionLocal()
    try:
        doc = (
            db.query(Document)
            .filter(Document.id == document_id, Document.user_id == user_id)
            .first()
        )
        if not doc:
            return {"success": False, "error": "Document not found"}

        # If already processed and not forcing, exit
        if doc.processed and not force:
            return {"success": True, "skipped": True, "document_id": document_id}

        doc.processing_status = "processing"
        doc.processing_error = None
        db.commit()

        host, port = _chroma_host_port()
        collection_name = ChromaDBService.user_collection_name(user_id)

        # If force reprocess: delete old vectors first
        if force:
            try:
                chroma = ChromaDBService(host=host, port=port)
                chroma.create_collection(collection_name)
                chroma.delete_where(collection_name, where={"document_id": document_id})
            except Exception:
                pass

        rag = RAGService(chromadb_host=host, chromadb_port=port)

        result = rag.process_document(
            file_path=doc.file_path,
            file_type=doc.file_type,
            document_id=document_id,
            collection_name=collection_name,
            metadata={
                "user_id": user_id,
                "original_filename": doc.original_filename,
            },
        )

        if result.get("success"):
            doc.processed = True
            doc.processing_status = "processed"
            doc.processed_at = datetime.utcnow()
            doc.processing_error = None
            db.commit()
            return {"success": True, "document_id": document_id, "details": result}

        # Pipeline returned failure
        doc.processing_status = "failed"
        doc.processing_error = result.get("error", "Unknown processing error")
        db.commit()
        return {"success": False, "document_id": document_id, "error": doc.processing_error}

    except Exception as e:
        # Unexpected crash
        try:
            if doc:
                doc.processing_status = "failed"
                doc.processing_error = str(e)
                db.commit()
        except Exception:
            pass
        return {"success": False, "document_id": document_id, "error": str(e)}

    finally:
        db.close()