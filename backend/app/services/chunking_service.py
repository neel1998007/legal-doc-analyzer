"""
Text Chunking Service for Legal Documents
Splits extracted text into overlapping chunks for RAG
"""
import re
from typing import List, Dict, Any


class ChunkingService:
    """Service for splitting documents into chunks"""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100
    ):
        """
        Initialize chunking service

        Args:
            chunk_size: Target size of each chunk in words
            chunk_overlap: Number of words to overlap between chunks
            min_chunk_size: Minimum words for a valid chunk
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def split_text(
        self,
        text: str,
        document_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks

        Args:
            text: The text to split
            document_id: ID of the source document
            metadata: Additional metadata for chunks

        Returns:
            List of chunk dictionaries
        """
        if not text or not text.strip():
            return []

        # Split into sentences first for better chunking
        sentences = self._split_into_sentences(text)

        # Group sentences into chunks
        chunks = self._create_chunks(sentences)

        # Create chunk objects with metadata
        chunk_objects = []
        for idx, chunk_text in enumerate(chunks):
            if len(chunk_text.split()) < self.min_chunk_size:
                continue

            chunk = {
                "chunk_id": f"{document_id}_chunk_{idx}" if document_id else f"chunk_{idx}",
                "document_id": document_id,
                "chunk_index": idx,
                "text": chunk_text,
                "word_count": len(chunk_text.split()),
                "char_count": len(chunk_text),
                "metadata": metadata or {}
            }
            chunk_objects.append(chunk)

        return chunk_objects

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        # Split on sentence boundaries
        sentence_endings = re.compile(
            r'(?<=[.!?])\s+(?=[A-Z])|(?<=\n)\s*(?=\d+\.)|(?<=\n)\s*(?=[A-Z])'
        )

        sentences = sentence_endings.split(text)

        # Clean up sentences
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def _create_chunks(self, sentences: List[str]) -> List[str]:
        """
        Group sentences into overlapping chunks

        Args:
            sentences: List of sentences

        Returns:
            List of chunk texts
        """
        if not sentences:
            return []

        chunks = []
        current_chunk_sentences = []
        current_word_count = 0

        for sentence in sentences:
            sentence_word_count = len(sentence.split())

            # If adding this sentence exceeds chunk size
            if current_word_count + sentence_word_count > self.chunk_size:
                # Save current chunk if it has content
                if current_chunk_sentences:
                    chunk_text = " ".join(current_chunk_sentences)
                    chunks.append(chunk_text)

                    # Create overlap: keep last N words
                    overlap_text = self._get_overlap(
                        current_chunk_sentences
                    )
                    current_chunk_sentences = (
                        [overlap_text] if overlap_text else []
                    )
                    current_word_count = len(
                        overlap_text.split()
                    ) if overlap_text else 0

            # Add sentence to current chunk
            current_chunk_sentences.append(sentence)
            current_word_count += sentence_word_count

        # Don't forget the last chunk
        if current_chunk_sentences:
            chunk_text = " ".join(current_chunk_sentences)
            chunks.append(chunk_text)

        return chunks

    def _get_overlap(self, sentences: List[str]) -> str:
        """
        Get the overlap text from end of current chunk

        Args:
            sentences: Current chunk sentences

        Returns:
            Overlap text
        """
        if not sentences:
            return ""

        # Get words from the end of current chunk
        all_text = " ".join(sentences)
        words = all_text.split()

        if len(words) <= self.chunk_overlap:
            return all_text

        overlap_words = words[-self.chunk_overlap:]
        return " ".join(overlap_words)

    def get_chunk_stats(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics about chunks

        Args:
            chunks: List of chunk objects

        Returns:
            Statistics dictionary
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "avg_word_count": 0,
                "min_word_count": 0,
                "max_word_count": 0,
                "total_words": 0
            }

        word_counts = [c["word_count"] for c in chunks]

        return {
            "total_chunks": len(chunks),
            "avg_word_count": sum(word_counts) // len(word_counts),
            "min_word_count": min(word_counts),
            "max_word_count": max(word_counts),
            "total_words": sum(word_counts)
        }