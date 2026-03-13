from __future__ import annotations

from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter


class Chunker:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 120) -> None:
        self.splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def split(self, text: str) -> list[str]:
        if not text.strip():
            return []
        chunks = [
            node.text.strip()
            for node in self.splitter.get_nodes_from_documents([Document(text=text)])
            if node.text.strip()
        ]
        if chunks:
            return [item for item in chunks if item]
        return self._fallback_split(text)

    def split_text(self, text: str) -> list[str]:
        return self.split(text)

    def _fallback_split(self, text: str) -> list[str]:
        normalized = text.strip()
        if not normalized:
            return []
        size = max(self.splitter.chunk_size, 200)
        overlap = min(self.splitter.chunk_overlap, size // 4)
        chunks: list[str] = []
        start = 0
        while start < len(normalized):
            end = min(start + size, len(normalized))
            chunks.append(normalized[start:end].strip())
            if end >= len(normalized):
                break
            start = max(end - overlap, start + 1)
        return [item for item in chunks if item]