from weasyprint import HTML
import tempfile
import os

from core.config import settings


class PDFService:
    @staticmethod
    async def generate_agreement_pdf(html_content: str, filename: str) -> str:
        """Generate a PDF from HTML content and save it to a temporary file."""
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".pdf", prefix=f"{filename}_"
        ) as temp_file:
            temp_path = temp_file.name

        HTML(string=html_content).write_pdf(temp_path)
        return temp_path

    @staticmethod
    async def cleanup_file(file_path: str) -> None:
        """Remove a temporary file."""
        if os.path.exists(file_path):
            os.remove(file_path)


pdf_service = PDFService()
