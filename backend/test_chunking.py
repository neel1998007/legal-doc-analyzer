"""
Test script for text chunking
Run with: python test_chunking.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.chunking_service import ChunkingService
from app.services.extraction_service import ExtractionService

# Sample legal document text for testing
SAMPLE_LEGAL_TEXT = """
LEGAL CONTRACT AGREEMENT

This agreement is entered into as of January 1, 2024, between Party A, 
hereinafter referred to as "the Client," and Party B, hereinafter 
referred to as "the Service Provider."

1. SCOPE OF SERVICES
The Service Provider agrees to provide legal consulting services as 
described in Exhibit A attached hereto. The services shall include but 
not be limited to contract review, legal research, and advisory services.

2. PAYMENT TERMS
The Client agrees to pay the Service Provider a monthly retainer of 
$5,000 USD. Payment shall be made within 30 days of receipt of invoice. 
Late payments shall accrue interest at a rate of 1.5% per month.

3. TERM AND TERMINATION
This agreement shall commence on January 1, 2024, and continue for a 
period of one year. Either party may terminate this agreement with 30 
days written notice. Upon termination, all outstanding fees shall 
become immediately due and payable.

4. CONFIDENTIALITY
Both parties agree to maintain strict confidentiality regarding all 
proprietary information shared during the course of this agreement. 
This obligation shall survive the termination of the agreement for 
a period of five years.

5. INTELLECTUAL PROPERTY
All work product created by the Service Provider shall remain the 
property of the Client upon full payment of all fees. The Service 
Provider retains the right to use general methodologies and 
non-confidential information for other clients.

6. LIMITATION OF LIABILITY
The Service Provider's liability under this agreement shall be 
limited to the total fees paid in the three months preceding the 
claim. Neither party shall be liable for indirect, incidental, 
or consequential damages.

7. GOVERNING LAW
This agreement shall be governed by and construed in accordance 
with the laws of the State of New York. Any disputes shall be 
resolved through binding arbitration in New York City.

8. ENTIRE AGREEMENT
This document constitutes the entire agreement between the parties 
and supersedes all prior negotiations, representations, or agreements. 
Any modifications must be made in writing and signed by both parties.
"""

def test_basic_chunking():
    """Test basic text chunking"""
    print("\n" + "="*50)
    print("🧪 TEST 1: Basic Chunking")
    print("="*50)
    
    chunker = ChunkingService(
        chunk_size=100,
        chunk_overlap=20,
        min_chunk_size=20
    )
    
    chunks = chunker.split_text(
        SAMPLE_LEGAL_TEXT,
        document_id="test_doc_001",
        metadata={"source": "test", "type": "contract"}
    )
    
    print(f"✅ Created {len(chunks)} chunks")
    print(f"📊 Stats: {chunker.get_chunk_stats(chunks)}")
    
    if chunks:
        print(f"\n📝 First chunk preview:")
        print(f"  ID: {chunks[0]['chunk_id']}")
        print(f"  Words: {chunks[0]['word_count']}")
        print(f"  Text: {chunks[0]['text'][:150]}...")
        return True
    else:
        print("❌ No chunks created")
        return False

def test_chunk_overlap():
    """Test that chunks have proper overlap"""
    print("\n" + "="*50)
    print("🧪 TEST 2: Chunk Overlap")
    print("="*50)
    
    chunker = ChunkingService(
        chunk_size=50,
        chunk_overlap=10,
        min_chunk_size=10
    )
    
    chunks = chunker.split_text(SAMPLE_LEGAL_TEXT)
    
    if len(chunks) >= 2:
        chunk1_words = chunks[0]['text'].split()
        chunk2_words = chunks[1]['text'].split()
        
        # Check if last words of chunk1 appear in chunk2
        last_words = chunk1_words[-5:]
        chunk2_text = chunks[1]['text']
        
        overlap_found = any(
            word in chunk2_text for word in last_words
        )
        
        print(f"✅ Created {len(chunks)} chunks with overlap")
        print(f"  Last words of chunk 1: {' '.join(last_words)}")
        print(f"  Overlap detected: {overlap_found}")
        return True
    else:
        print("⚠️ Not enough chunks to test overlap")
        return False

def test_legal_document_chunking():
    """Test chunking with real extracted document"""
    print("\n" + "="*50)
    print("🧪 TEST 3: Legal Document Chunking")
    print("="*50)
    
    # Check if test document exists
    docx_path = "./test_documents/test_contract.docx"
    
    if not os.path.exists(docx_path):
        print("⚠️ Test document not found, using sample text")
        text = SAMPLE_LEGAL_TEXT
    else:
        # Extract text from document
        text = ExtractionService.extract_from_docx(docx_path)
        print(f"✅ Extracted {len(text)} characters from document")
    
    # Use smaller chunk settings for small test document
    chunker = ChunkingService(
        chunk_size=30,      # Smaller chunks for small test doc
        chunk_overlap=5,    # Smaller overlap
        min_chunk_size=10   # Allow small chunks
    )
    
    chunks = chunker.split_text(
        text,
        document_id="legal_contract_001",
        metadata={
            "document_type": "contract",
            "source_file": "test_contract.docx"
        }
    )
    
    stats = chunker.get_chunk_stats(chunks)
    
    print(f"✅ Created {stats['total_chunks']} chunks")
    print(f"📊 Average words per chunk: {stats['avg_word_count']}")
    print(f"📊 Total words processed: {stats['total_words']}")
    
    return len(chunks) > 0

def test_chunk_metadata():
    """Test that chunks have proper metadata"""
    print("\n" + "="*50)
    print("🧪 TEST 4: Chunk Metadata")
    print("="*50)
    
    chunker = ChunkingService()
    
    metadata = {
        "document_type": "contract",
        "source_file": "test.pdf",
        "upload_date": "2024-01-01"
    }
    
    chunks = chunker.split_text(
        SAMPLE_LEGAL_TEXT,
        document_id="doc_123",
        metadata=metadata
    )
    
    if chunks:
        first_chunk = chunks[0]
        
        # Check required fields
        required_fields = [
            "chunk_id", "document_id", "chunk_index",
            "text", "word_count", "char_count", "metadata"
        ]
        
        all_fields_present = all(
            field in first_chunk for field in required_fields
        )
        
        print(f"✅ All required fields present: {all_fields_present}")
        print(f"✅ Document ID correct: {first_chunk['document_id'] == 'doc_123'}")
        print(f"✅ Metadata preserved: {first_chunk['metadata'] == metadata}")
        
        return all_fields_present
    
    return False

def test_empty_text():
    """Test handling of empty text"""
    print("\n" + "="*50)
    print("🧪 TEST 5: Empty Text Handling")
    print("="*50)
    
    chunker = ChunkingService()
    
    # Test with empty string
    chunks = chunker.split_text("")
    print(f"✅ Empty string returns {len(chunks)} chunks (expected 0)")
    
    # Test with whitespace
    chunks = chunker.split_text("   \n\n   ")
    print(f"✅ Whitespace returns {len(chunks)} chunks (expected 0)")
    
    return True

def main():
    """Main test function"""
    print("✂️ Legal Document Analyzer - Chunking Test")
    print("="*50)
    
    tests_passed = 0
    total_tests = 5
    
    if test_basic_chunking():
        tests_passed += 1
    
    if test_chunk_overlap():
        tests_passed += 1
    
    if test_legal_document_chunking():
        tests_passed += 1
    
    if test_chunk_metadata():
        tests_passed += 1
    
    if test_empty_text():
        tests_passed += 1
    
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    print(f"✅ Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Ready for embeddings!")
    else:
        print("⚠️ Some tests failed. Check errors above.")

if __name__ == "__main__":
    main()