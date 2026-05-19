from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, documents, rag
from app.core.database import test_connection

app = FastAPI(
    title="Legal Document Analyzer",
    description="A local RAG application for analyzing legal documents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(rag.router)


@app.get("/")
async def root():
    return {
        "message": "Legal Document Analyzer API",
        "version": "1.0.0",
        "status": "running",
        "docs": "Visit /docs for API documentation",
    }


@app.get("/health")
async def health_check():
    db_status = "connected" if test_connection() else "disconnected"
    return {"status": "healthy", "database": db_status, "services": "operational"}


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error": "HTTP Exception"},
    )