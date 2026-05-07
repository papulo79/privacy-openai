"""Reconstructor de archivos de texto plano (.txt) anonimizados."""

from io import BytesIO
from typing import List

from anonymizer.builders.base import BaseBuilder
from anonymizer.extractors.base import ExtractedText


class TxtBuilder(BaseBuilder):
    """Reconstruye un archivo de texto plano con el contenido anonimizado."""

    def build(
        self,
        original_stream: BytesIO,
        extracted_texts: List[ExtractedText],
        redacted_texts: List[str],
    ) -> BytesIO:
        # Solo hay un bloque de texto
        output = BytesIO()
        if redacted_texts:
            output.write(redacted_texts[0].encode("utf-8"))
        output.seek(0)
        return output
