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

    let selectedFile = null;

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
            alert('Unsupported file type. Please upload TXT, MD, DOCX, or PDF files.');
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

    // Upload + convert
    convertBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        convertBtn.disabled = true;
        convertBtn.textContent = 'Uploading...';

        try {
            const formData = new FormData();
            formData.append('file', selectedFile);

            const uploadResp = await fetch('/api/upload', {
                method: 'POST',
                body: formData,
            });

            if (!uploadResp.ok) {
                const err = await uploadResp.json();
                throw new Error(err.detail || 'Upload failed');
            }

            const uploadData = await uploadResp.json();
            const jobId = uploadData.job_id;

            // Start conversion
            const convertResp = await fetch(`/api/convert/${jobId}`, {
                method: 'POST',
            });

            if (!convertResp.ok) {
                const err = await convertResp.json();
                throw new Error(err.detail || 'Failed to start conversion');
            }

            // Hand off to conversion.js for progress tracking
            if (window.startProgressTracking) {
                window.startProgressTracking(jobId);
            }

        } catch (err) {
            alert('Error: ' + err.message);
            convertBtn.disabled = false;
            convertBtn.textContent = 'Start Conversion';
        }
    });
})();
