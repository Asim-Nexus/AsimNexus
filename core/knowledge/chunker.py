"""
AsimNexus — Recursive Character Text Splitter
==============================================
Splits text into chunks for RAG ingestion. Nepali-aware (respects 「।」).
"""

import re
from typing import List, Optional


class RecursiveCharacterTextSplitter:
    """
    Splits text recursively using a list of separators.
    Falls back to character-level splitting if all separators fail.
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", "。", ".", " "]

    def split_text(self, text: str) -> List[str]:
        """Split text into chunks."""
        if not text:
            return []

        return self._split_recursive(text, self.separators)

    def _split_recursive(self, text: str, separators: List[str]) -> List[str]:
        """Recursively split using the list of separators."""
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []

        if not separators:
            return self._split_by_chars(text)

        separator = separators[0]
        remaining_separators = separators[1:]

        if separator == "":
            return self._split_by_chars(text)

        chunks = self._split_with_separator(text, separator)

        # If splitting didn't help, try next separator
        if len(chunks) == 1:
            return self._split_recursive(text, remaining_separators)

        result = []
        for chunk in chunks:
            if len(chunk) > self.chunk_size:
                result.extend(self._split_recursive(chunk, remaining_separators))
            else:
                if chunk.strip():
                    result.append(chunk)
        return self._merge_chunks(result)

    def _split_with_separator(self, text: str, separator: str) -> List[str]:
        """Split text using a separator, keeping the separator with the chunk."""
        if separator == "":
            return list(text)

        parts = text.split(separator)
        result = []
        for i, part in enumerate(parts):
            if i < len(parts) - 1:
                result.append(part + separator)
            else:
                result.append(part)
        return [r for r in result if r.strip()]

    def _split_by_chars(self, text: str) -> List[str]:
        """Split text by character count."""
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunks.append(text[start:end])
            start = end - self.chunk_overlap if end < len(text) else len(text)
        return chunks

    def _merge_chunks(self, chunks: List[str]) -> List[str]:
        """Merge small chunks back up to chunk_size."""
        merged = []
        current = ""
        for chunk in chunks:
            if len(current) + len(chunk) <= self.chunk_size:
                current += chunk
            else:
                if current:
                    merged.append(current)
                current = chunk
        if current:
            merged.append(current)
        return merged
