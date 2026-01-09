import os
from pypdf import PdfReader
from fastapi import UploadFile

class PDFService:
    def __init__(self, upload_dir: str = "data/uploads"):
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)

    async def save_pdf(self, file: UploadFile) -> str:
        """
        Saves the uploaded file to disk and returns the file path.
        """
        file_path = os.path.join(self.upload_dir, file.filename)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
            
        return file_path

    def extract_text(self, file_path: str) -> str:
        """
        Extracts raw text from the saved PDF file.
        """
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text.strip()
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""