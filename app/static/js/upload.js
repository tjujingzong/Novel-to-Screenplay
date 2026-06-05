/* Upload page: file selection and drag-drop handling */

(function () {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const fileMeta = document.getElementById('file-meta');
    const removeBtn = document.getElementById('remove-file');
    const convertSection = document.getElementById('convert-section');
    const convertBtn = document.getElementById('convert-btn');
    const apiKeyInput = document.getElementById('api-key-input');
    const toggleApiKeyBtn = document.getElementById('toggle-api-key');

    let selectedFile = null;

    // Load cached API key from localStorage
    const cachedApiKey = localStorage.getItem('deepseek_api_key');
    if (cachedApiKey) {
        apiKeyInput.value = cachedApiKey;
    }

    // Toggle API key visibility
    toggleApiKeyBtn.addEventListener('click', () => {
        const isPassword = apiKeyInput.type === 'password';
        apiKeyInput.type = isPassword ? 'text' : 'password';
    });

    // Click to browse
    dropZone.addEventListener('click', () => fileInput.click());

    // Drag events
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });

    // File input change
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            handleFile(fileInput.files[0]);
        }
    });

    // Remove file
    removeBtn.addEventListener('click', () => {
        selectedFile = null;
        fileInput.value = '';
        fileInfo.classList.add('hidden');
        convertSection.classList.add('hidden');
        dropZone.classList.remove('hidden');
    });

    function handleFile(file) {
        const validExts = ['.txt', '.md', '.markdown', '.docx', '.pdf'];
        const ext = '.' + file.name.split('.').pop().toLowerCase();

        if (!validExts.includes(ext)) {
            alert('不支持的文件类型。请上传 TXT、MD、DOCX 或 PDF 文件。');
            return;
        }

        selectedFile = file;
        fileName.textContent = file.name;

        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
        fileMeta.textContent = `${ext.toUpperCase().slice(1)} - ${sizeMB} MB`;

        dropZone.classList.add('hidden');
        fileInfo.classList.remove('hidden');
        convertSection.classList.remove('hidden');
    }

    // Expose for sample novels
    window.handleSampleFile = handleFile;

    // Upload + convert
    convertBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        convertBtn.disabled = true;
        convertBtn.textContent = '上传中...';

        try {
            const formData = new FormData();
            formData.append('file', selectedFile);

            const uploadResp = await fetch('/api/upload', {
                method: 'POST',
                body: formData,
            });

            if (!uploadResp.ok) {
                const err = await uploadResp.json();
                throw new Error(err.detail || '上传失败');
            }

            const uploadData = await uploadResp.json();
            const jobId = uploadData.job_id;

            // Start conversion
            const apiKey = apiKeyInput.value.trim();

            // Store API key for editor page
            if (apiKey) {
                sessionStorage.setItem('api_key', apiKey);
                localStorage.setItem('deepseek_api_key', apiKey);
            }

            const convertResp = await fetch(`/api/convert/${jobId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: apiKey }),
            });

            if (!convertResp.ok) {
                const err = await convertResp.json();
                throw new Error(err.detail || '启动转换失败');
            }

            // Hand off to conversion.js for progress tracking
            if (window.startProgressTracking) {
                window.startProgressTracking(jobId);
            }

        } catch (err) {
            alert('错误：' + err.message);
            convertBtn.disabled = false;
            convertBtn.textContent = '开始转换';
        }
    });
})();
