import os
import uuid
from typing import Optional, Tuple
from pathlib import Path
import PyPDF2
import docx
from .config import settings


class FileProcessor:
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)
    
    def is_allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return Path(filename).suffix.lower() in settings.ALLOWED_EXTENSIONS
    
    def generate_unique_filename(self, original_filename: str) -> str:
        """Generate unique filename while preserving extension"""
        ext = Path(original_filename).suffix
        unique_name = f"{uuid.uuid4()}{ext}"
        return unique_name
    
    def save_file(self, file_content: bytes, filename: str) -> str:
        """Save file to upload directory"""
        file_path = self.upload_dir / filename
        with open(file_path, "wb") as f:
            f.write(file_content)
        return str(file_path)
    
    def extract_text_from_pdf(self, file_path: str) -> Optional[str]:
        """Extract text from PDF file"""
        try:
            text = ""
            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return None
    
    def extract_text_from_docx(self, file_path: str) -> Optional[str]:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            print(f"Error extracting text from DOCX: {e}")
            return None
    
    def extract_text_from_txt(self, file_path: str) -> Optional[str]:
        """Extract text from TXT file"""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read().strip()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, "r", encoding="latin-1") as file:
                    return file.read().strip()
            except Exception as e:
                print(f"Error reading TXT file: {e}")
                return None
        except Exception as e:
            print(f"Error extracting text from TXT: {e}")
            return None
    
    def extract_text(self, file_path: str, file_type: str) -> Optional[str]:
        """Extract text based on file type"""
        if file_type.lower() == ".pdf":
            return self.extract_text_from_pdf(file_path)
        elif file_type.lower() == ".docx":
            return self.extract_text_from_docx(file_path)
        elif file_type.lower() == ".txt":
            return self.extract_text_from_txt(file_path)
        else:
            return None
    
    def process_uploaded_file(self, file_content: bytes, original_filename: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Process uploaded file and return file_path, filename, and extracted text"""
        try:
            # Check if file is allowed
            if not self.is_allowed_file(original_filename):
                return None, None, None
            
            # Generate unique filename
            unique_filename = self.generate_unique_filename(original_filename)
            
            # Save file
            file_path = self.save_file(file_content, unique_filename)
            
            # Extract text
            file_type = Path(original_filename).suffix.lower()
            extracted_text = self.extract_text(file_path, file_type)
            
            return file_path, unique_filename, extracted_text
            
        except Exception as e:
            print(f"Error processing uploaded file: {e}")
            return None, None, None
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file from filesystem"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False


# Global file processor instance
file_processor = FileProcessor()
