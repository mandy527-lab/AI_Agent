from io import BytesIO

import pytest

from src.resume_parser import extract_resume_text


def named_file(content: bytes, name: str) -> BytesIO:
    file = BytesIO(content)
    file.name = name
    return file


def test_extracts_utf8_text_resume():
    file = named_file("Python 開發經驗".encode(), "resume.txt")

    assert extract_resume_text(file) == "Python 開發經驗"


def test_rejects_unsupported_extension():
    file = named_file(b"content", "resume.pages")

    with pytest.raises(ValueError, match="只支援"):
        extract_resume_text(file)

