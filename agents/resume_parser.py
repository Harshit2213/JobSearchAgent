import io

import pdfplumber
from docx import Document
from fastapi import HTTPException

from agents.base import BaseAgent
from models.resume import ParsedResume

_MIME_PDF = "application/pdf"

_EXTRACT_TOOL = {
    "name": "extract_resume",
    "description": "Extract structured information from resume text.",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "email": {"type": "string"},
            "skills": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Professional skills (soft + hard)",
            },
            "tech_stack": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Languages, frameworks, and tools",
            },
            "years_of_experience": {
                "type": "number",
                "description": "Total years of professional experience",
            },
            "past_titles": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Job titles held, most recent first",
            },
            "education": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Degrees and institutions",
            },
            "summary": {
                "type": "string",
                "description": "2-3 sentence professional summary",
            },
        },
        "required": [
            "name", "skills", "tech_stack",
            "past_titles", "years_of_experience", "education", "summary",
        ],
    },
}

_SYSTEM = (
    "You are a resume parser. Extract structured information accurately from the resume text. "
    "Use only information explicitly present — do not infer or fabricate details. "
    "If a field is not present, use an empty string or empty list."
)


class ResumeParserAgent(BaseAgent):
    _quality = "high"
    def parse(self, content: bytes, mime: str) -> ParsedResume:
        raw_text = self._extract_text(content, mime)
        if not raw_text.strip():
            raise HTTPException(status_code=422, detail="Could not extract text from the uploaded file.")

        response = self._call(
            system=_SYSTEM,
            messages=[{"role": "user", "content": f"Parse this resume:\n\n{raw_text}"}],
            tools=[_EXTRACT_TOOL],
            tool_name="extract_resume",
            cache_system=True,
        )
        data = self._extract_tool_input(response)
        return ParsedResume(**data, raw_text=raw_text)

    def _extract_text(self, content: bytes, mime: str) -> str:
        if mime == _MIME_PDF:
            return self._from_pdf(content)
        return self._from_docx(content)

    def _from_pdf(self, content: bytes) -> str:
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                pages = [page.extract_text() or "" for page in pdf.pages]
            return "\n".join(pages).strip()
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Failed to read PDF: {exc}") from exc

    def _from_docx(self, content: bytes) -> str:
        try:
            doc = Document(io.BytesIO(content))
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Failed to read DOCX: {exc}") from exc
