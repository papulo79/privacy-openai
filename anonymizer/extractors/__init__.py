"""Init de extractores."""

from anonymizer.extractors.base import BaseExtractor, ExtractedText
from anonymizer.extractors.docx import DocxExtractor
from anonymizer.extractors.xlsx import XlsxExtractor
from anonymizer.extractors.pptx import PptxExtractor
from anonymizer.extractors.txt import TxtExtractor

__all__ = [
    "BaseExtractor",
    "ExtractedText",
    "DocxExtractor",
    "XlsxExtractor",
    "PptxExtractor",
    "TxtExtractor",
]
