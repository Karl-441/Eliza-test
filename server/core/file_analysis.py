import os
import logging
import hashlib
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class FileAnalyzer:
    def __init__(self):
        self.supported_extensions = {
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".py": "text/x-python",
            ".json": "application/json",
            ".csv": "text/csv",
            ".pdf": "application/pdf"
        }
        
    def _calculate_hash(self, file_path: str) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _security_scan(self, file_path: str, content_preview: bytes) -> Dict[str, Any]:
        """
        Basic heuristic security scan.
        """
        scan_results = {
            "safe": True,
            "issues": []
        }
        
        # 1. Check Magic Numbers / Extension mismatch (Simplified)
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf" and not content_preview.startswith(b"%PDF"):
            scan_results["issues"].append("Invalid PDF header")
            scan_results["safe"] = False
            
        # 2. Check for suspicious content in text files
        if ext in [".txt", ".md", ".py", ".json", ".csv"]:
            try:
                text = content_preview.decode('utf-8', errors='ignore')
                suspicious_patterns = ["eval(", "exec(", "os.system(", "subprocess.Popen("]
                found = [p for p in suspicious_patterns if p in text]
                if found and ext != ".py": # Python files naturally have these, maybe warn but not flag unsafe immediately
                    scan_results["issues"].append(f"Suspicious code patterns found: {found}")
                    scan_results["safe"] = False
            except:
                pass
                
        return scan_results

    def extract_text(self, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == ".pdf":
            try:
                from pypdf import PdfReader
                reader = PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
            except Exception as e:
                logger.error(f"PDF extraction error: {e}")
                return f"[Error extracting PDF: {str(e)}]"
        
        elif ext in self.supported_extensions:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Text extraction error: {e}")
                return f"[Error reading file: {str(e)}]"
                
        return "[Unsupported file format for text extraction]"

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            return {"error": "File not found"}
            
        stats = os.stat(file_path)
        file_hash = self._calculate_hash(file_path)
        
        # Read first 2KB for scan
        with open(file_path, "rb") as f:
            preview = f.read(2048)
            
        security_report = self._security_scan(file_path, preview)
        
        text_content = ""
        if security_report["safe"]:
            text_content = self.extract_text(file_path)
            # Truncate for summary if too long
            summary = text_content[:500] + "..." if len(text_content) > 500 else text_content
        else:
            summary = "[Content hidden due to security flags]"

        return {
            "filename": os.path.basename(file_path),
            "size": stats.st_size,
            "hash": file_hash,
            "security": security_report,
            "content_preview": summary,
            "full_text_length": len(text_content)
        }

file_analyzer = FileAnalyzer()
