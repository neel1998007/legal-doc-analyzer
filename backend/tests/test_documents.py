"""
Tests for document upload and management
"""
import pytest
import os
import tempfile
from fastapi.testclient import TestClient

class TestDocumentEndpoints:
    """Test document upload and management"""
    
    def test_upload_pdf_file(self, client: TestClient, test_user, auth_headers):
        """Test uploading a PDF file"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(b"Test PDF content for upload testing")
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, "rb") as file:
                response = client.post(
                    "/documents/upload",
                    files={"file": ("test.pdf", file, "application/pdf")},
                    headers=auth_headers
                )
            
            assert response.status_code == 201
            data = response.json()
            assert data["original_filename"] == "test.pdf"
            assert data["file_type"] == "application/pdf"
            assert data["user_id"] == str(test_user["id"])  # Use dict access
            assert data["processed"] is False
            assert data["file_size"] > 0
            
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)

    def test_upload_docx_file(self, client: TestClient, test_user, auth_headers):
        """Test uploading a DOCX file"""
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_file:
            tmp_file.write(b"Test DOCX content")
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, "rb") as file:
                response = client.post(
                    "/documents/upload",
                    files={
                        "file": (
                            "test.docx",
                            file,
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                    },
                    headers=auth_headers
                )
            
            assert response.status_code == 201
            data = response.json()
            assert data["original_filename"] == "test.docx"
            # Fix: Check for the full MIME type
            assert "wordprocessingml" in data["file_type"]
            
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)

    def test_upload_invalid_file_type(self, client: TestClient, auth_headers):
        """Test uploading invalid file type"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp_file:
            tmp_file.write(b"Test text content")
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, "rb") as file:
                response = client.post(
                    "/documents/upload",
                    files={"file": ("test.txt", file, "text/plain")},
                    headers=auth_headers
                )
            
            assert response.status_code == 400
            assert "not allowed" in response.json()["detail"]
            
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)


    def test_upload_no_auth(self, client: TestClient):
        """Test uploading without authentication"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(b"Test content")
            tmp_file_path = tmp_file.name

        try:
            with open(tmp_file_path, "rb") as file:
                response = client.post(
                    "/documents/upload",
                    files={"file": ("test.pdf", file, "application/pdf")}
                )
            assert response.status_code == 401

        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)      


    def test_list_documents(self, client: TestClient, auth_headers):
        """Test listing user documents"""
        response = client.get("/documents/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_documents_no_auth(self, client: TestClient):
        """Test listing documents without authentication"""
        response = client.get("/documents/")
        
        assert response.status_code == 401

    def test_get_document_stats(self, client: TestClient, auth_headers):
        """Test getting document statistics"""
        response = client.get("/documents/stats/summary", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_documents" in data
        assert "processed_documents" in data
        assert "pending_documents" in data
        assert "total_storage_bytes" in data
        assert "total_storage_mb" in data

    def test_upload_large_file(self, client: TestClient, auth_headers):
        """Test uploading file larger than limit"""
        # Create file larger than MAX_FILE_SIZE (10MB = 10485760 bytes)
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB - bigger than 10MB limit
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(large_content)
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, "rb") as file:
                response = client.post(
                    "/documents/upload",
                    files={"file": ("large.pdf", file, "application/pdf")},
                    headers=auth_headers
                )
            
            assert response.status_code == 413
            
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)