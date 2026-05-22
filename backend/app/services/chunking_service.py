"""
Text Chunking Service for Legal Documents
Splits extracted text into overlapping chunks for RAG
"""
import re
from typing import List, Dict, Any, Optional


class ChunkingService:
    """Service for splitting documents into chunks"""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def split_text(
        self,
        text: str,
        document_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks.
        Production rule: if text is non-empty but chunking yields 0 chunks,
        return a single fallback chunk (for short documents).
        """
        if not text or not text.strip():
            return []

        metadata = metadata or {}

        total_words = len(text.split())

        # Split into sentences first for better chunk boundaries
        sentences = self._split_into_sentences(text)

        # Create raw chunk texts
        chunk_texts = self._create_chunks(sentences)

        # Build chunk objects, filtering out tiny chunks
        chunk_objects: List[Dict[str, Any]] = []
        for idx, chunk_text in enumerate(chunk_texts):
            wc = len(chunk_text.split())
            if wc < self.min_chunk_size:
                continue

            chunk_objects.append({
                "chunk_id": f"{document_id}_chunk_{idx}" if document_id else f"chunk_{idx}",
                "document_id": document_id,
                "chunk_index": idx,
                "text": chunk_text,
                "word_count": wc,
                "char_count": len(chunk_text),
                "metadata": metadata
            })

        # ✅ Fallback for short documents (business critical)
        if not chunk_objects and total_words > 0:
            fallback_text = text.strip()
            chunk_objects.append({
                "chunk_id": f"{document_id}_chunk_0" if document_id else "chunk_0",
                "document_id": document_id,
                "chunk_index": 0,
                "text": fallback_text,
                "word_count": len(fallback_text.split()),
                "char_count": len(fallback_text),
                "metadata": metadata
            })

        return chunk_objects

    def _split_into_sentences(self, text: str) -> List[str]:
        # Split on sentence boundaries + numbered headings
        sentence_endings = re.compile(
            r'(?<=[.!?])\s+(?=[A-Z])|(?<=\n)\s*(?=\d+\.)|(?<=\n)\s*(?=[A-Z])'
        )
        sentences = sentence_endings.split(text)
        return [s.strip() for s in sentences if s.strip()]

    def _create_chunks(self, sentences: List[str]) -> List[str]:
        if not sentences:
            return []

        chunks: List[str] = []
        current: List[str] = []
        current_wc = 0

        for sentence in sentences:
            swc = len(sentence.split())

            # if adding sentence exceeds chunk_size → flush chunk
            if current and (current_wc + swc > self.chunk_size):
                chunks.append(" ".join(current))

                # overlap: keep last N words from current chunk
                overlap_text = self._get_overlap(current)
                current = [overlap_text] if overlap_text else []
                current_wc = len(overlap_text.split()) if overlap_text else 0

            current.append(sentence)
            current_wc += swc

        if current:
            chunks.append(" ".join(current))

        return chunks

    def _get_overlap(self, sentences: List[str]) -> str:
        all_text = " ".join(sentences).strip()
        if not all_text:
            return ""

        words = all_text.split()
        if len(words) <= self.chunk_overlap:
            return all_text

        return " ".join(words[-self.chunk_overlap:])

    def get_chunk_stats(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
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