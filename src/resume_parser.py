from io import BytesIO
from pathlib import Path
from typing import BinaryIO

from docx import Document
from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def _read_bytes(uploaded_file: BinaryIO) -> bytes:
    uploaded_file.seek(0)
    return uploaded_file.read()


def extract_resume_text(uploaded_file: BinaryIO) -> str:
    """Extract text from a Streamlit uploaded PDF, DOCX, or TXT file."""
    filename = getattr(uploaded_file, "name", "")
    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("目前只支援 PDF、DOCX 與 TXT 履歷。")

    file_bytes = _read_bytes(uploaded_file)

    if extension == ".txt":
        try:
            return file_bytes.decode("utf-8").strip()
        except UnicodeDecodeError as error:
            raise ValueError("TXT 履歷請使用 UTF-8 編碼。") from error

    if extension == ".pdf":
        reader = PdfReader(BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()

    document = Document(BytesIO(file_bytes))
    return "\n".join(paragraph.text for paragraph in document.paragraphs).strip()

