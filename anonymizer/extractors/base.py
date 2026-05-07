"""Extractores de texto de documentos."""

from abc import ABC, abstractmethod
from io import BytesIO
from typing import List, Tuple


class ExtractedText:
    """Representa un fragmento de texto extraído con su contexto de ubicación."""

    def __init__(self, text: str, location: Tuple):
        self.text = text
        self.location = location


class BaseExtractor(ABC):
    """Interfaz base para extractores de documentos."""

    @abstractmethod
    def extract(self, file_stream: BytesIO) -> List[ExtractedText]:
        """Extrae todos los fragmentos de texto de un documento.

        Args:
            file_stream: Stream en memoria con el archivo.

        Returns:
            Lista de ExtractedText con el texto y su ubicación.
        """
        ...
