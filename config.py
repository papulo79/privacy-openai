"""Configuración global de la aplicación."""

import os

# Flask
FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5042"))
MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", "50")) * 1024 * 1024  # 50 MB

# OPF (OpenAI Privacy Filter)
OPF_DEVICE = os.getenv("OPF_DEVICE", "cpu")
OPF_OUTPUT_MODE = os.getenv("OPF_OUTPUT_MODE", "redacted")
OPF_DECODE_MODE = os.getenv("OPF_DECODE_MODE", "viterbi")
OPF_CHECKPOINT = os.getenv(
    "OPF_CHECKPOINT",
    os.path.expanduser("~/.opf/privacy_filter/original"),
)
OPF_TRANSFORMER = os.getenv("OPF_TRANSFORMER", "redacted")

# Tipos de archivo soportados
SUPPORTED_EXTENSIONS = {
    ".docx": "word",
    ".xlsx": "excel",
    ".pptx": "powerpoint",
    ".txt": "text",
}

SUPPORTED_MIMETYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "word",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "excel",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "powerpoint",
    "text/plain": "text",
}
