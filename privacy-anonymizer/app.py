"""Aplicación Flask para anonimización de documentos con OpenAI Privacy Filter."""

import os
import time
from io import BytesIO
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

import config
from anonymizer.engine import AnonymizerEngine
from anonymizer.extractors import DocxExtractor, PptxExtractor, TxtExtractor, XlsxExtractor
from anonymizer.builders import DocxBuilder, PptxBuilder, TxtBuilder, XlsxBuilder
from anonymizer.transformers import list_transformers

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH

# Inicializar motor de anonimización (lazy load)
_engine: AnonymizerEngine | None = None


def get_engine() -> AnonymizerEngine:
    """Devuelve el motor de anonimización, inicializándolo si es necesario."""
    global _engine
    if _engine is None:
        _engine = AnonymizerEngine()
    return _engine


# Mapeo de tipos a extractor/builder
_PROCESSORS = {
    "word": (DocxExtractor(), DocxBuilder()),
    "excel": (XlsxExtractor(), XlsxBuilder()),
    "powerpoint": (PptxExtractor(), PptxBuilder()),
    "text": (TxtExtractor(), TxtBuilder()),
}


def _detect_file_type(filename: str, mimetype: str) -> str | None:
    """Detecta el tipo de documento por extensión o MIME type."""
    ext = Path(filename).suffix.lower()
    if ext in config.SUPPORTED_EXTENSIONS:
        return config.SUPPORTED_EXTENSIONS[ext]
    if mimetype in config.SUPPORTED_MIMETYPES:
        return config.SUPPORTED_MIMETYPES[mimetype]
    return None


@app.route("/")
def index():
    """Página principal con la UI de subida."""
    return render_template("index.html", transformers=list_transformers())


@app.route("/health")
def health():
    """Endpoint de salud: verifica que el modelo opf esté cargado."""
    try:
        engine = get_engine()
        return jsonify({
            "status": "ok",
            "model_ready": engine.is_ready,
            "transformer": engine.transformer_name,
            "available_transformers": list_transformers(),
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 503


@app.route("/anonymize", methods=["POST"])
def anonymize():
    """Recibe un archivo, lo anonimiza y devuelve el resultado.

    Query params:
        transformer: Nombre del transformador a usar (redacted, initials, hash, partial).
                     Si no se especifica, usa el configurado por defecto.

    No escribe NUNCA el archivo en disco. Todo el procesamiento ocurre en memoria.
    """
    start_time = time.time()

    if "file" not in request.files:
        return jsonify({"error": "No se proporcionó ningún archivo."}), 400

    uploaded = request.files["file"]
    if not uploaded.filename:
        return jsonify({"error": "El archivo está vacío."}), 400

    file_type = _detect_file_type(uploaded.filename, uploaded.content_type or "")
    if file_type is None:
        return (
            jsonify(
                {
                    "error": "Formato no soportado.",
                    "supported": list(config.SUPPORTED_EXTENSIONS.keys()),
                }
            ),
            415,
        )

    # Obtener transformador solicitado
    transformer_name = request.args.get("transformer", config.OPF_TRANSFORMER)
    try:
        engine = get_engine()
        engine.set_transformer(transformer_name)
    except ValueError as e:
        return jsonify({
            "error": str(e),
            "available": list_transformers(),
        }), 400

    try:
        # Leer archivo en memoria
        file_stream = BytesIO(uploaded.read())

        # Extraer texto
        extractor, builder = _PROCESSORS[file_type]
        extracted = extractor.extract(file_stream)

        # Anonimizar cada fragmento
        redacted = [engine.redact(item.text) for item in extracted]

        # Reconstruir documento
        output_stream = builder.build(file_stream, extracted, redacted)

        # Preparar nombre de salida
        stem = Path(uploaded.filename).stem
        suffix = Path(uploaded.filename).suffix
        output_filename = f"{stem}_anonimizado{suffix}"

        # Headers de privacidad: evitar caché
        response = send_file(
            output_stream,
            as_attachment=True,
            download_name=output_filename,
            mimetype=uploaded.content_type or "application/octet-stream",
        )
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["X-Content-Type-Options"] = "nosniff"

        elapsed = time.time() - start_time
        app.logger.info(
            "Anonimizado: %s (%s, transformer=%s, %d fragmentos, %.2fs)",
            uploaded.filename,
            file_type,
            transformer_name,
            len(extracted),
            elapsed,
        )

        return response

    except Exception as e:
        app.logger.exception("Error anonimizando archivo")
        return jsonify({"error": f"Error procesando el archivo: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=False)
