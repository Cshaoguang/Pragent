from __future__ import annotations

from io import BytesIO
from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader


class DocumentParser:
    async def parse(self, file_name: str, content: bytes) -> str:
        suffix = Path(file_name).suffix.lower()
        if suffix == ".pdf":
            return self._parse_pdf(content)
        if suffix == ".docx":
            return self._parse_docx(content)
        if suffix in {".md", ".markdown", ".txt"}:
            return content.decode("utf-8", errors="ignore")
        raise ValueError(f"不支持的文件类型: {suffix}")

    def _parse_pdf(self, content: bytes) -> str:
        reader = PdfReader(BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()

    def _parse_docx(self, content: bytes) -> str:
        document = DocxDocument(BytesIO(content))
        lines = [paragraph.text for paragraph in document.paragraphs if paragraph.text]
        return "\n".join(lines).strip()