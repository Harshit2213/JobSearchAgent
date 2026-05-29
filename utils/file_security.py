import io
import os
import re

import filetype
from fastapi import HTTPException, UploadFile

_ALLOWED_MIMES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
_MAX_FILENAME_LEN = 128


async def validate_upload(file: UploadFile, max_bytes: int) -> tuple[bytes, str]:
    """Read, size-check, MIME-check, and return (bytes, mime_type). Raises HTTPException on violation."""
    content = await file.read()

    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {max_bytes // (1024 * 1024)} MB.",
        )

    kind = filetype.guess(content)
    if kind is None or kind.mime not in _ALLOWED_MIMES:
        raise HTTPException(
            status_code=422,
            detail="Only PDF and DOCX files are accepted.",
        )

    return content, kind.mime


def safe_filename(name: str) -> str:
    """Strip path components and allow only safe characters."""
    name = os.path.basename(name)
    name = re.sub(r"[^a-zA-Z0-9._\-]", "_", name)
    return name[:_MAX_FILENAME_LEN]


def bytes_to_stream(content: bytes) -> io.BytesIO:
    return io.BytesIO(content)
