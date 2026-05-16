"""
Test script for embedding generation
Run with: python test_embeddings.py
"""
import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.embedding_service import EmbeddingService
from app.services.chunking_service import ChunkingService

SAMPLE_LEGAL_TEXT = """
LEGAL CONTRACT AGREEMENT

This agreement is entered into as of January 1, 2024, between Party A,
hereinafter referred to as the Client, and Party B, hereinafter
referred to as the Service Provider.

1. PAYMENT TERMS
Payment shall be made within 30 days of receipt of invoice.
Late payments shall accrue interest at a rate of 1.5% per month.

2. TERMINATION
Either party may terminate this agreement with 30 days written notice.
Upon termination, all outstanding fees shall become immediately due.

3. CONFIDENTIALITY
Both parties agree to maintain strict confidentiality regarding all
proprietary information shared during the course of this agreement.
"""

def test_single_embedding():
    """Test generating a single embedding"""
    print("\n" + "="*50)
    print("🧪 TEST 1: Single Embedding Generation")
    print("="*50)

    text = "What is the payment term for this contract?"

    start_time = time.time()
    embedding = EmbeddingService.generate_embedding(text)
    elapsed = time.time() - start_time

    print(f"✅ Generated embedding in {elapsed:.2f} seconds")
    print(f"📊 Embedding dimensions: {len(embedding)}")
    print(f"📊 Sample values: {embedding[:5]}")

    # Verify it's a list of floats
    assert isinstance(embedding, list), "Embedding should be a list"
    assert len(embedding) == 384, f"Expected 384 dimensions, got {len(embedding)}"
    assert all(isinstance(x, float) for x in embedding), "All values should be floats"

    print("✅ Embedding format correct!")
    return True

def test_batch_embeddings():
    """Test batch embedding generation"""
    print("\n" + "="*50)
    print("🧪 TEST 2: Batch Embedding Generation")
    print("="*50)

    texts = [
        "What is the payment term?",
        "How can the contract be terminated?",
        "What are the confidentiality requirements?",
        "Who are the parties to this agreement?",
    ]

    start_time = time.time()
    embeddings = EmbeddingService.generate_embeddings_batch(texts)
    elapsed = time.time() - start_time

    print(f"✅ Generated {len(embeddings)} embeddings in {elapsed:.2f} seconds")
    print(f"📊 Each embedding has {len(embeddings[0])} dimensions")

    assert len(embeddings) == len(texts), "Should have one embedding per text"
    print("✅ Batch embedding correct!")
    return True

def test_similarity():
    """Test similarity calculation"""
    print("\n" + "="*50)
    print("🧪 TEST 3: Similarity Calculation")
    print("="*50)

    # Similar texts should have high similarity
    text1 = "Payment must be made within 30 days"
    text2 = "Invoice payment is due in 30 days"
    text3 = "The contract can be terminated with notice"

    emb1 = EmbeddingService.generate_embedding(text1)
    emb2 = EmbeddingService.generate_embedding(text2)
    emb3 = EmbeddingService.generate_embedding(text3)

    sim_12 = EmbeddingService.calculate_similarity(emb1, emb2)
    sim_13 = EmbeddingService.calculate_similarity(emb1, emb3)

    print(f"📊 Similarity (payment texts): {sim_12:.4f}")
    print(f"📊 Similarity (payment vs termination): {sim_13:.4f}")

    # Payment texts should be more similar to each other
    assert sim_12 > sim_13, "Similar texts should have higher similarity"
    print("✅ Similarity calculation correct!")
    return True

def test_chunk_embedding():
    """Test embedding chunks from document"""
    print("\n" + "="*50)
    print("🧪 TEST 4: Chunk Embedding")
    print("="*50)

    # Create chunks
    chunker = ChunkingService(
        chunk_size=50,
        chunk_overlap=10,
        min_chunk_size=10
    )

    chunks = chunker.split_text(
        SAMPLE_LEGAL_TEXT,
        document_id="test_doc",
        metadata={"type": "contract"}
    )

    print(f"📝 Created {len(chunks)} chunks")

    # Embed chunks
    embedded_chunks = EmbeddingService.embed_chunks(chunks)

    print(f"✅ Embedded {len(embedded_chunks)} chunks")
    print(f"📊 Embedding dimension: {embedded_chunks[0]['embedding_dimension']}")
    print(f"📊 Model used: {embedded_chunks[0]['embedding_model']}")

    # Verify all chunks have embeddings
    assert all("embedding" in c for c in embedded_chunks)
    assert all(len(c["embedding"]) == 384 for c in embedded_chunks)
    print("✅ All chunks embedded correctly!")
    return True

def test_semantic_search():
    """Test finding relevant chunks for a query"""
    print("\n" + "="*50)
    print("🧪 TEST 5: Semantic Search")
    print("="*50)

    # Create and embed chunks
    chunker = ChunkingService(
        chunk_size=50,
        chunk_overlap=10,
        min_chunk_size=10
    )

    chunks = chunker.split_text(SAMPLE_LEGAL_TEXT, document_id="test_doc")
    embedded_chunks = EmbeddingService.embed_chunks(chunks)

    # Search for relevant chunks
    query = "What are the payment terms?"
    query_embedding = EmbeddingService.generate_embedding(query)

    # Get all chunk embeddings
    chunk_embeddings = [c["embedding"] for c in embedded_chunks]

    # Find most similar
    results = EmbeddingService.find_most_similar(
        query_embedding,
        chunk_embeddings,
        top_k=3
    )

    print(f"📝 Query: '{query}'")
    print(f"\n🔍 Top {len(results)} relevant chunks:")

    for i, result in enumerate(results):
        chunk = embedded_chunks[result["index"]]
        print(f"\n  Result {i+1} (similarity: {result['similarity']:.4f}):")
        print(f"  {chunk['text'][:150]}...")

    assert len(results) > 0, "Should find at least one result"
    print("\n✅ Semantic search working!")
    return True

def main():
    """Main test function"""
    print("🤖 Legal Document Analyzer - Embedding Test")
    print("="*50)
    print("Note: First run downloads the model (~90MB)")

    tests_passed = 0
    total_tests = 5

    if test_single_embedding():
        tests_passed += 1

    if test_batch_embeddings():
        tests_passed += 1

    if test_similarity():
        tests_passed += 1

    if test_chunk_embedding():
        tests_passed += 1

    if test_semantic_search():
        tests_passed += 1

    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    print(f"✅ Tests passed: {tests_passed}/{total_tests}")

    if tests_passed == total_tests:
        print("🎉 All tests passed! Ready for ChromaDB!")
    else:
        print("⚠️ Some tests failed. Check errors above.")

if __name__ == "__main__":
    main()