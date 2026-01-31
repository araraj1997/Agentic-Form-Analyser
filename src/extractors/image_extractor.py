"""
Image Extractor Module

Handles extraction of text from image files using OCR.
"""

from typing import Tuple, List, Dict, Any
from pathlib import Path


class ImageExtractor:
    """
    Extracts text from image files using OCR (Tesseract).
    
    Supports:
    - PNG, JPG, JPEG, TIFF, BMP formats
    - Multi-language OCR
    - Image preprocessing for better accuracy
    """
    
    def __init__(self, language: str = 'eng', preprocess: bool = True):
        """
        Initialize image extractor.
        
        Args:
            language: OCR language code (e.g., 'eng', 'deu', 'fra')
            preprocess: Whether to preprocess images for better OCR
        """
        self.language = language
        self.preprocess = preprocess
        self._pytesseract = None
        self._Image = None
        self._cv2 = None
        self._np = None
    
    def _lazy_imports(self):
        """Lazy import dependencies."""
        if self._pytesseract is None:
            try:
                import pytesseract
                from PIL import Image
                self._pytesseract = pytesseract
                self._Image = Image
            except ImportError:
                raise ImportError(
                    "pytesseract and Pillow are required. "
                    "Install with: pip install pytesseract Pillow"
                )
        
        if self._cv2 is None and self.preprocess:
            try:
                import cv2
                import numpy as np
                self._cv2 = cv2
                self._np = np
            except ImportError:
                # OpenCV optional for preprocessing
                pass
    
    def extract(self, file_path: str) -> Tuple[str, List[List[List[str]]], Dict[str, Any]]:
        """
        Extract content from an image file.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Tuple of (raw_text, tables, metadata)
        """
        self._lazy_imports()
        
        raw_text = ""
        tables = []
        metadata = {}
        
        try:
            # Load image
            image = self._Image.open(file_path)
            
            # Store metadata
            metadata = {
                'format': image.format,
                'mode': image.mode,
                'size': image.size,
                'file_path': file_path
            }
            
            # Preprocess if enabled and OpenCV available
            if self.preprocess and self._cv2 is not None:
                image = self._preprocess_image(image)
            
            # Perform OCR
            raw_text = self._pytesseract.image_to_string(
                image, 
                lang=self.language,
                config='--psm 6'  # Assume uniform block of text
            )
            
            # Try to extract tables using Tesseract's TSV output
            tables = self._extract_table_structure(image)
            
            # Get OCR confidence
            ocr_data = self._pytesseract.image_to_data(
                image, 
                lang=self.language,
                output_type=self._pytesseract.Output.DICT
            )
            
            confidences = [
                int(c) for c in ocr_data['conf'] 
                if c != '-1' and str(c).isdigit()
            ]
            if confidences:
                metadata['average_confidence'] = sum(confidences) / len(confidences)
            
        except Exception as e:
            metadata['error'] = str(e)
        
        return raw_text.strip(), tables, metadata
    
    def _preprocess_image(self, image):
        """
        Preprocess image for better OCR accuracy.
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image
        """
        if self._cv2 is None or self._np is None:
            return image
        
        # Convert PIL to OpenCV format
        img_array = self._np.array(image)
        
        # Convert to grayscale if needed
        if len(img_array.shape) == 3:
            gray = self._cv2.cvtColor(img_array, self._cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Apply thresholding
        _, thresh = self._cv2.threshold(
            gray, 0, 255, 
            self._cv2.THRESH_BINARY + self._cv2.THRESH_OTSU
        )
        
        # Denoise
        denoised = self._cv2.fastNlMeansDenoising(thresh)
        
        # Convert back to PIL
        return self._Image.fromarray(denoised)
    
    def _extract_table_structure(self, image) -> List[List[List[str]]]:
        """
        Attempt to extract table structure from image.
        
        Args:
            image: PIL Image object
            
        Returns:
            List of detected tables
        """
        tables = []
        
        try:
            # Use Tesseract's TSV output to detect table structure
            tsv_data = self._pytesseract.image_to_data(
                image,
                lang=self.language,
                output_type=self._pytesseract.Output.DICT
            )
            
            # Group by block and paragraph to find potential table rows
            current_row = []
            current_top = -1
            row_tolerance = 10
            
            potential_table = []
            
            for i, text in enumerate(tsv_data['text']):
                if not text.strip():
                    continue
                
                top = tsv_data['top'][i]
                
                if current_top == -1:
                    current_top = top
                
                # Check if same row (similar vertical position)
                if abs(top - current_top) <= row_tolerance:
                    current_row.append(text.strip())
                else:
                    if len(current_row) >= 2:  # Potential table row
                        potential_table.append(current_row)
                    current_row = [text.strip()]
                    current_top = top
            
            # Add last row
            if len(current_row) >= 2:
                potential_table.append(current_row)
            
            # If we have multiple rows with similar column counts, it's likely a table
            if len(potential_table) >= 2:
                col_counts = [len(row) for row in potential_table]
                most_common = max(set(col_counts), key=col_counts.count)
                
                # Filter to rows with consistent column count
                consistent_rows = [
                    row for row in potential_table 
                    if len(row) == most_common or abs(len(row) - most_common) <= 1
                ]
                
                if len(consistent_rows) >= 2:
                    tables.append(consistent_rows)
        
        except Exception:
            pass
        
        return tables
    
    def extract_text_only(self, file_path: str) -> str:
        """
        Extract only text from an image.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Extracted text
        """
        text, _, _ = self.extract(file_path)
        return text
