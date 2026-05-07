"""Motor de anonimización basado en OpenAI Privacy Filter (opf)."""

import threading
from typing import Optional

from opf import OPF

import config
from anonymizer.transformers import BaseTransformer, get_transformer


class AnonymizerEngine:
    """Singleton thread-safe del motor de anonimización opf."""

    _instance: Optional["AnonymizerEngine"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "AnonymizerEngine":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        # Usamos output_mode='typed' para obtener etiquetas de los spans
        self._opf = OPF(
            model=config.OPF_CHECKPOINT,
            device=config.OPF_DEVICE,
            output_mode="typed",
            decode_mode=config.OPF_DECODE_MODE,
            output_text_only=False,
        )
        self._transformer: BaseTransformer = get_transformer(config.OPF_TRANSFORMER)
        self._initialized = True

    def set_transformer(self, name: str) -> None:
        """Cambia el transformador activo.

        Args:
            name: Nombre del transformador a usar.
        """
        self._transformer = get_transformer(name)

    @property
    def transformer_name(self) -> str:
        """Devuelve el nombre del transformador activo."""
        for name, t in get_transformer.__globals__.get("TRANSFORMERS", {}).items():
            if t is self._transformer:
                return name
        return "unknown"

    def redact(self, text: str) -> str:
        """Anonimiza un texto plano aplicando el transformador configurado.

        Args:
            text: Texto a anonimizar.

        Returns:
            Texto con la información personal transformada.
        """
        if not text or not text.strip():
            return text

        result = self._opf.redact(text)

        # Si no hay spans, devolver el texto original
        if not result.detected_spans:
            return result.text

        # Aplicar transformaciones personalizadas span por span
        # Ordenar spans de derecha a izquierda para no desplazar índices
        sorted_spans = sorted(
            result.detected_spans,
            key=lambda s: s.start,
            reverse=True,
        )

        output = result.text
        for span in sorted_spans:
            transformed = self._transformer.transform(span.text, span.label)
            output = output[: span.start] + transformed + output[span.end :]

        return output

    @property
    def is_ready(self) -> bool:
        """Devuelve True si el modelo está cargado y listo."""
        return self._initialized
