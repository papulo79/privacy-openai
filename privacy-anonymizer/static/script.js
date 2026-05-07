document.addEventListener('DOMContentLoaded', () => {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const btnSelect = document.getElementById('btnSelect');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const btnRemove = document.getElementById('btnRemove');
    const btnAnonymize = document.getElementById('btnAnonymize');
    const btnText = btnAnonymize.querySelector('.btn-text');
    const spinner = document.getElementById('spinner');
    const resultArea = document.getElementById('resultArea');
    const resultFilename = document.getElementById('resultFilename');
    const errorArea = document.getElementById('errorArea');
    const errorMessage = document.getElementById('errorMessage');
    const transformerSelect = document.getElementById('transformerSelect');
    const transformerHelp = document.getElementById('transformerHelp');

    let currentFile = null;

    const transformerDescriptions = {
        redacted: 'Reemplaza toda la información personal detectada por <REDACTED>.',
        initials: 'Convierte nombres a iniciales (A.J.), emails parciales (a***@e***.com), teléfonos enmascarados (555-***-4567).',
        partial: 'Muestra solo el inicio de cada dato: A**** J*******, 555-***-4567, a****@e*****.com.',
        hash: 'Genera un identificador hash único y consistente para cada dato detectado. Útil para correlacionar sin revelar.',
    };

    function formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    function resetUI() {
        currentFile = null;
        fileInput.value = '';
        uploadArea.style.display = 'block';
        fileInfo.style.display = 'none';
        btnAnonymize.disabled = true;
        resultArea.style.display = 'none';
        errorArea.style.display = 'none';
    }

    function showFile(file) {
        currentFile = file;
        fileName.textContent = file.name;
        fileSize.textContent = formatBytes(file.size);
        uploadArea.style.display = 'none';
        fileInfo.style.display = 'flex';
        btnAnonymize.disabled = false;
        resultArea.style.display = 'none';
        errorArea.style.display = 'none';
    }

    function setLoading(loading) {
        btnAnonymize.disabled = loading;
        btnText.textContent = loading ? 'Procesando...' : 'Anonimizar y descargar';
        spinner.style.display = loading ? 'inline-block' : 'none';
    }

    function showError(msg) {
        errorMessage.textContent = msg;
        errorArea.style.display = 'block';
        resultArea.style.display = 'none';
    }

    function showSuccess(filename) {
        resultFilename.textContent = filename;
        resultArea.style.display = 'block';
        errorArea.style.display = 'none';
    }

    // Actualizar descripción del transformador
    transformerSelect.addEventListener('change', () => {
        const selected = transformerSelect.value;
        transformerHelp.textContent = transformerDescriptions[selected] || '';
    });

    // Drag & drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.classList.remove('dragover');
        });
    });

    uploadArea.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            showFile(files[0]);
        }
    });

    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    btnSelect.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            showFile(fileInput.files[0]);
        }
    });

    btnRemove.addEventListener('click', resetUI);

    btnAnonymize.addEventListener('click', async () => {
        if (!currentFile) return;

        setLoading(true);
        errorArea.style.display = 'none';

        const formData = new FormData();
        formData.append('file', currentFile);

        const transformer = transformerSelect.value;
        const url = `/anonymize?transformer=${encodeURIComponent(transformer)}`;

        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                let msg = 'Error desconocido';
                try {
                    const data = await response.json();
                    msg = data.error || `Error ${response.status}`;
                } catch {
                    msg = `Error ${response.status}: ${response.statusText}`;
                }
                throw new Error(msg);
            }

            const blob = await response.blob();
            const contentDisposition = response.headers.get('content-disposition');
            let downloadName = currentFile.name.replace(/(\.[a-zA-Z0-9]+)$/, '_anonimizado$1');
            if (contentDisposition) {
                const match = contentDisposition.match(/filename="?([^"]+)"?/);
                if (match) downloadName = match[1];
            }

            const urlObj = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = urlObj;
            a.download = downloadName;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(urlObj);

            showSuccess(downloadName);
        } catch (err) {
            showError(err.message);
        } finally {
            setLoading(false);
        }
    });
});
