"""
Argument Preprocessing Module
Validates, cleans, and structures legal arguments for the AI Judge system
"""

import re
from typing import List, Dict, Tuple, Optional
from enum import Enum
import PyPDF2
import docx
import io
from fastapi import HTTPException, UploadFile

class ArgumentFormat(Enum):
    """Supported argument formatting styles"""
    NUMBERED = "numbered"  # 1. 2. 3.
    LETTERED = "lettered"  # a. b. c. or A. B. C.
    ROMAN = "roman"        # i. ii. iii. or I. II. III.
    BULLET = "bullet"      # - or * or •
    PARAGRAPH = "paragraph"  # No specific formatting


class FileValidator:
    """Validates uploaded files"""
    
    ALLOWED_EXTENSIONS = {'.txt', '.pdf', '.docx', '.doc'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def validate_extension(filename: str) -> bool:
        """Check if file extension is allowed"""
        ext = filename[filename.rfind('.'):].lower() if '.' in filename else ''
        return ext in FileValidator.ALLOWED_EXTENSIONS
    
    @staticmethod
    def validate_file_size(content: bytes) -> bool:
        """Check if file size is within limits"""
        return len(content) <= FileValidator.MAX_FILE_SIZE
    
    @staticmethod
    async def validate_file(file: UploadFile) -> Tuple[bool, Optional[str]]:
        """
        Validate uploaded file
        Returns: (is_valid, error_message)
        """
        # Check extension
        if not FileValidator.validate_extension(file.filename):
            allowed = ', '.join(FileValidator.ALLOWED_EXTENSIONS)
            return False, f"Invalid file type. Allowed types: {allowed}"
        
        # Read content for size check
        content = await file.read()
        await file.seek(0)  # Reset file pointer
        
        # Check size
        if not FileValidator.validate_file_size(content):
            max_mb = FileValidator.MAX_FILE_SIZE / (1024 * 1024)
            return False, f"File too large. Maximum size: {max_mb}MB"
        
        return True, None


class ArgumentExtractor:
    """Extracts text from various file formats"""
    
    @staticmethod
    def extract_from_pdf(content: bytes) -> str:
        """Extract text from PDF"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")
    
    @staticmethod
    def extract_from_docx(content: bytes) -> str:
        """Extract text from DOCX"""
        try:
            doc = docx.Document(io.BytesIO(content))
            text = "\n".join([para.text for para in doc.paragraphs])
            return text.strip()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading DOCX: {str(e)}")
    
    @staticmethod
    def extract_from_txt(content: bytes) -> str:
        """Extract text from TXT"""
        try:
            return content.decode('utf-8').strip()
        except UnicodeDecodeError:
            try:
                return content.decode('latin-1').strip()
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error reading text file: {str(e)}")
    
    @staticmethod
    def extract_text(content: bytes, filename: str) -> str:
        """Extract text based on file extension"""
        ext = filename[filename.rfind('.'):].lower() if '.' in filename else ''
        
        if ext == '.pdf':
            return ArgumentExtractor.extract_from_pdf(content)
        elif ext in ['.docx', '.doc']:
            return ArgumentExtractor.extract_from_docx(content)
        elif ext == '.txt':
            return ArgumentExtractor.extract_from_txt(content)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")


class ArgumentParser:
    """Parses and structures arguments from text"""
    
    # Regex patterns for different argument formats
    PATTERNS = {
        ArgumentFormat.NUMBERED: r'^\s*(\d+)[\.\)\:]',
        ArgumentFormat.LETTERED: r'^\s*([a-zA-Z])[\.\)\:]',
        ArgumentFormat.ROMAN: r'^\s*([ivxIVX]+)[\.\)\:]',
        ArgumentFormat.BULLET: r'^\s*[\-\*\•\◦\▪]',
    }
    
    @staticmethod
    def detect_format(text: str) -> ArgumentFormat:
        """Detect the argument formatting style"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        format_counts = {fmt: 0 for fmt in ArgumentFormat}
        
        for line in lines[:20]:  # Check first 20 lines
            for fmt, pattern in ArgumentParser.PATTERNS.items():
                if re.match(pattern, line):
                    format_counts[fmt] += 1
        
        # Return format with highest count, default to PARAGRAPH
        max_format = max(format_counts.items(), key=lambda x: x[1])
        return max_format[0] if max_format[1] > 0 else ArgumentFormat.PARAGRAPH
    
    @staticmethod
    def extract_points(text: str, format_type: ArgumentFormat) -> List[Dict[str, str]]:
        """Extract individual argument points"""
        if format_type == ArgumentFormat.PARAGRAPH:
            # Split by double newlines for paragraphs
            paragraphs = re.split(r'\n\s*\n', text)
            return [
                {"index": str(i+1), "content": p.strip()} 
                for i, p in enumerate(paragraphs) if p.strip()
            ]
        
        pattern = ArgumentParser.PATTERNS.get(format_type)
        if not pattern:
            return []
        
        points = []
        current_point = {"index": "", "content": ""}
        
        for line in text.split('\n'):
            match = re.match(pattern, line)
            if match:
                # Save previous point if exists
                if current_point["content"]:
                    points.append(current_point)
                # Start new point
                current_point = {
                    "index": match.group(1) if match.groups() else str(len(points) + 1),
                    "content": re.sub(pattern, '', line).strip()
                }
            elif current_point["content"] or current_point["index"]:
                # Continue current point
                current_point["content"] += " " + line.strip()
        
        # Add last point
        if current_point["content"]:
            points.append(current_point)
        
        return points
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters that might interfere
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        return text.strip()


class ArgumentSequencer:
    """Manages the sequence and ordering of arguments"""
    
    @staticmethod
    def process_argument_sequence(arguments: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Process arguments in sequence: Side A, Side B, Side A, Side B, etc.
        
        Args:
            arguments: List of argument dicts with 'side', 'text', 'order' fields
            
        Returns:
            Structured dict with alternating sides and proper ordering
        """
        # Sort by order field
        sorted_args = sorted(arguments, key=lambda x: x.get('order', 0))
        
        side_a = []
        side_b = []
        
        expected_side = 'A'
        for i, arg in enumerate(sorted_args, 1):
            side = arg.get('side', '').upper()
            
            # Validate alternating pattern
            if i > 1 and side == sorted_args[i-2].get('side', '').upper():
                # Allow multiple consecutive arguments from same side, but warn
                arg['warning'] = f"Multiple consecutive arguments from Side {side}"
            
            if side == 'A':
                side_a.append(arg)
            elif side == 'B':
                side_b.append(arg)
            
            expected_side = 'B' if expected_side == 'A' else 'A'
        
        return {
            'side_a': side_a,
            'side_b': side_b,
            'total_rounds': max(len(side_a), len(side_b)),
            'is_balanced': len(side_a) == len(side_b)
        }
    
    @staticmethod
    def validate_argument_balance(side_a_count: int, side_b_count: int, 
                                   max_difference: int = 1) -> Tuple[bool, Optional[str]]:
        """
        Validate that both sides have roughly equal number of arguments
        
        Returns: (is_valid, warning_message)
        """
        diff = abs(side_a_count - side_b_count)
        
        if diff > max_difference:
            return False, f"Imbalanced arguments: Side A has {side_a_count}, Side B has {side_b_count}"
        
        if diff == max_difference:
            return True, f"Side {'A' if side_a_count > side_b_count else 'B'} has one more argument"
        
        return True, None


class ArgumentPreprocessor:
    """Main preprocessing pipeline"""
    
    def __init__(self):
        self.validator = FileValidator()
        self.extractor = ArgumentExtractor()
        self.parser = ArgumentParser()
        self.sequencer = ArgumentSequencer()
    
    async def process_file(self, file: UploadFile) -> Dict:
        """
        Complete preprocessing pipeline for a single file
        
        Returns:
            {
                'filename': str,
                'raw_text': str,
                'cleaned_text': str,
                'format': ArgumentFormat,
                'points': List[Dict],
                'metadata': Dict
            }
        """
        # Step 1: Validate file
        is_valid, error = await self.validator.validate_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)
        
        # Step 2: Extract text
        content = await file.read()
        raw_text = self.extractor.extract_text(content, file.filename)
        
        if not raw_text or len(raw_text.strip()) < 10:
            raise HTTPException(status_code=400, detail="File is empty or contains insufficient text")
        
        # Step 3: Clean text
        cleaned_text = self.parser.clean_text(raw_text)
        
        # Step 4: Detect format
        format_type = self.parser.detect_format(cleaned_text)
        
        # Step 5: Extract points
        points = self.parser.extract_points(cleaned_text, format_type)
        
        # Step 6: Generate metadata
        metadata = {
            'word_count': len(cleaned_text.split()),
            'char_count': len(cleaned_text),
            'point_count': len(points),
            'format_detected': format_type.value,
            'file_size_kb': len(content) / 1024
        }
        
        return {
            'filename': file.filename,
            'raw_text': raw_text,
            'cleaned_text': cleaned_text,
            'format': format_type.value,
            'points': points,
            'metadata': metadata
        }
    
    async def process_multiple_files(self, files: List[UploadFile], side: str) -> Dict:
        """
        Process multiple files for a side
        
        Returns:
            {
                'side': str,
                'files': List[Dict],
                'combined_text': str,
                'total_points': int,
                'summary': Dict
            }
        """
        processed_files = []
        all_points = []
        combined_text = ""
        
        for file in files:
            processed = await self.process_file(file)
            processed_files.append(processed)
            all_points.extend(processed['points'])
            combined_text += processed['cleaned_text'] + "\n\n"
        
        summary = {
            'file_count': len(files),
            'total_words': sum(f['metadata']['word_count'] for f in processed_files),
            'total_points': len(all_points),
            'formats_used': list(set(f['format'] for f in processed_files))
        }
        
        return {
            'side': side.upper(),
            'files': processed_files,
            'combined_text': combined_text.strip(),
            'all_points': all_points,
            'summary': summary
        }
    
    def validate_case_arguments(self, side_a_data: Dict, side_b_data: Dict) -> Dict:
        """
        Validate complete case arguments from both sides
        
        Returns validation report with any warnings or issues
        """
        issues = []
        warnings = []
        
        # Check if both sides have arguments
        if not side_a_data.get('combined_text'):
            issues.append("Side A has no arguments")
        if not side_b_data.get('combined_text'):
            issues.append("Side B has no arguments")
        
        # Check balance
        side_a_points = len(side_a_data.get('all_points', []))
        side_b_points = len(side_b_data.get('all_points', []))
        
        is_balanced, balance_msg = self.sequencer.validate_argument_balance(
            side_a_points, side_b_points, max_difference=2
        )
        
        if not is_balanced:
            issues.append(balance_msg)
        elif balance_msg:
            warnings.append(balance_msg)
        
        # Check word counts
        side_a_words = side_a_data.get('summary', {}).get('total_words', 0)
        side_b_words = side_b_data.get('summary', {}).get('total_words', 0)
        
        if abs(side_a_words - side_b_words) > side_a_words * 0.5:  # 50% difference
            warnings.append(f"Significant word count difference: A={side_a_words}, B={side_b_words}")
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'statistics': {
                'side_a': {
                    'points': side_a_points,
                    'words': side_a_words,
                    'files': side_a_data.get('summary', {}).get('file_count', 0)
                },
                'side_b': {
                    'points': side_b_points,
                    'words': side_b_words,
                    'files': side_b_data.get('summary', {}).get('file_count', 0)
                }
            }
        }


# Singleton instance
preprocessor = ArgumentPreprocessor()
