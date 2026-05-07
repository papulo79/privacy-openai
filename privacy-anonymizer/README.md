# Anonimizador de Documentos con OpenAI Privacy Filter

Aplicación web para anonimizar documentos Word, Excel, PowerPoint y texto plano utilizando el modelo [OpenAI Privacy Filter](https://github.com/openai/privacy-filter). Los documentos se procesan **únicamente en memoria** y nunca se almacenan en el servidor.

## Características

- **Formatos soportados**: Word (.docx), Excel (.xlsx), PowerPoint (.pptx), Texto plano (.txt)
- **Sin persistencia**: Todo el procesamiento ocurre en memoria (BytesIO). Cero escritura en disco.
- **Múltiples modos de anonimización**:
  - **Redactado**: Reemplaza todo por `<REDACTED>`
  - **Iniciales**: Convierte nombres a iniciales (A.J.), emails parciales, teléfonos enmascarados
  - **Máscara parcial**: Muestra el inicio de cada dato (A**** J*******)
  - **Hash**: Genera identificadores únicos consistentes para correlacionar sin revelar
- **API REST**: Endpoint `/anonymize` con soporte para selección de transformador
- **UI web**: Interfaz drag & drop con selección de modo de anonimización

## Requisitos

- Python >= 3.10
- ~6GB de espacio en disco (para el modelo de ~2.7GB + ONNX)
- ~2GB de RAM mínimo (4GB recomendado)

## Instalación

### 1. Clonar o copiar el proyecto

```bash
cd privacy-anonymizer
```

### 2. Instalar dependencias

```bash
# Instalar PyTorch (CPU-only recomendado para servidores sin GPU)
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Instalar opf desde el repositorio oficial
pip install git+https://github.com/openai/privacy-filter.git

# Instalar dependencias de la aplicación
pip install -r requirements.txt
```

### 3. Descargar el modelo

El modelo se descarga automáticamente en el primer uso a `~/.opf/privacy_filter/`. 

**Nota importante**: La librería `opf` espera el checkpoint en formato nativo (carpeta `original/`), no el formato Transformers/ONNX de la raíz del repositorio. Si la descarga automática falla, descárgalo manualmente:

```bash
python3 -c "
from huggingface_hub import hf_hub_download
import os

target = os.path.expanduser('~/.opf/privacy_filter')
os.makedirs(target, exist_ok=True)

# Descargar archivos del formato original
hf_hub_download(repo_id='openai/privacy-filter', filename='original/config.json', local_dir=target)
hf_hub_download(repo_id='openai/privacy-filter', filename='original/model.safetensors', local_dir=target)
"
```

### 4. Verificar instalación

```bash
python3 -c "
from anonymizer.engine import AnonymizerEngine
engine = AnonymizerEngine()
print(engine.redact('Alice Johnson, alice@email.com, 555-123-4567'))
"
```

## Uso

### Desarrollo

```bash
python app.py
```

La aplicación estará disponible en `http://0.0.0.0:5042`

### Producción con Gunicorn

```bash
gunicorn --bind 0.0.0.0:5042 --workers 1 --threads 4 --timeout 300 wsgi:app
```

### Systemd

1. Copiar el servicio:
```bash
sudo cp systemd/privacy-anonymizer.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now privacy-anonymizer
```

2. Verificar estado:
```bash
sudo systemctl status privacy-anonymizer
sudo journalctl -u privacy-anonymizer -f
```

### Cloudflare Tunnel

```bash
# Tunnel temporal
cloudflared tunnel --url http://127.0.0.1:5042

# Tunnel permanente (recomendado)
cloudflared tunnel create privacy-anonymizer
cloudflared tunnel route dns privacy-anonymizer tu-dominio.com
cloudflared tunnel run privacy-anonymizer
```

## API

### Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/` | Interfaz web |
| `GET` | `/health` | Estado del servicio |
| `POST` | `/anonymize` | Anonimizar documento |

### POST /anonymize

**Parámetros de query:**
- `transformer` (opcional): Modo de anonimización. Valores: `redacted`, `initials`, `partial`, `hash`. Default: `redacted`

**Form data:**
- `file`: Archivo a anonimizar

**Ejemplo con curl:**
```bash
curl -X POST "http://localhost:5042/anonymize?transformer=initials" \
  -F "file=@documento.docx" \
  --output documento_anonimizado.docx
```

## Variables de Entorno

| Variable | Default | Descripción |
|---|---|---|
| `FLASK_HOST` | `0.0.0.0` | Host de escucha |
| `FLASK_PORT` | `5042` | Puerto |
| `MAX_CONTENT_LENGTH` | `50` | Tamaño máximo de archivo en MB |
| `OPF_DEVICE` | `cpu` | Dispositivo de inferencia (`cpu` o `cuda`) |
| `OPF_TRANSFORMER` | `redacted` | Transformador por defecto |
| `OPF_CHECKPOINT` | `~/.opf/privacy_filter/original` | Ruta al checkpoint del modelo |

## Modos de Anonimización

### Redactado (`redacted`)
```
Alice Johnson → <REDACTED>
alice@email.com → <REDACTED>
555-123-4567 → <REDACTED>
```

### Iniciales (`initials`)
```
Alice Johnson → A.J.
alice@email.com → a***@e***.com
555-123-4567 → 555*****67
123 Main Street → 123 M. S.
15/03/1990 → **/**/****
https://example.com → https://*****.com
ES91 2345... → **** ****... 8901
```

### Máscara parcial (`partial`)
```
Alice Johnson → A**** J*******
alice@email.com → a****@e*****.com
555-123-4567 → 555*****67
```

### Hash (`hash`)
```
Alice Johnson → [PRIVATE_PERSON:5157f619]
alice@email.com → [PRIVATE_EMAIL:55bf4952]
```

Útil para correlacionar ocurrencias del mismo dato sin revelar el valor real.

## Arquitectura

```
privacy-anonymizer/
├── app.py                    # Flask app
├── wsgi.py                   # Entrypoint Gunicorn
├── config.py                 # Configuración
├── requirements.txt          # Dependencias
├── anonymizer/
│   ├── engine.py             # Motor de anonimización (singleton opf)
│   ├── transformers/         # Transformadores de anonimización
│   │   └── __init__.py       # Redacted, Initials, Partial, Hash
│   ├── extractors/           # Extraen texto de cada formato
│   │   ├── docx.py
│   │   ├── xlsx.py
│   │   ├── pptx.py
│   │   └── txt.py
│   └── builders/             # Reconstruyen documentos
│       ├── docx.py
│       ├── xlsx.py
│       ├── pptx.py
│       └── txt.py
├── static/
│   ├── style.css
│   └── script.js
├── templates/
│   └── index.html
└── systemd/
    └── privacy-anonymizer.service
```

## Privacidad y Seguridad

- **Sin persistencia**: Los archivos se procesan en memoria mediante `io.BytesIO`. Nunca se escriben en disco.
- **Sin logs de contenido**: Solo se registran metadatos (nombre, tamaño, tipo), nunca el contenido.
- **Headers anti-caché**: Las respuestas incluyen `Cache-Control: no-store` y `Pragma: no-cache`.
- **Procesamiento local**: El modelo opf se ejecuta localmente. Ningún dato sale del servidor.

## Licencia

Este proyecto utiliza el modelo [OpenAI Privacy Filter](https://github.com/openai/privacy-filter) bajo licencia Apache 2.0.
