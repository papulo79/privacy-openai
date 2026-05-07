"""Extractor de texto para archivos de texto plano (.txt)."""

from io import BytesIO
from typing import List

from anonymizer.extractors.base import BaseExtractor, ExtractedText


class TxtExtractor(BaseExtractor):
    """Extrae texto de archivos de texto plano."""

    def extract(self, file_stream: BytesIO) -> List[ExtractedText]:
        content = file_stream.read().decode("utf-8", errors="replace")
        # Devolvemos el contenido completo como un único bloque
        return [ExtractedText(text=content, location=("content",))]
