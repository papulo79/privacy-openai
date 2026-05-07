"""Reconstructores de documentos anonimizados."""

from abc import ABC, abstractmethod
from io import BytesIO
from typing import List

from anonymizer.extractors.base import ExtractedText


class BaseBuilder(ABC):
    """Interfaz base para reconstructores de documentos."""

    @abstractmethod
    def build(
        self,
        original_stream: BytesIO,
        extracted_texts: List[ExtractedText],
        redacted_texts: List[str],
    ) -> BytesIO:
        """Reconstruye el documento reemplazando el texto original por el anonimizado.

        Args:
            original_stream: Stream en memoria con el archivo original.
            extracted_texts: Lista de textos extraídos con su ubicación.
            redacted_texts: Lista de textos anonimizados (mismo orden que extracted_texts).

        Returns:
            Nuevo stream en memoria con el documento reconstruido.
        """
        ...
