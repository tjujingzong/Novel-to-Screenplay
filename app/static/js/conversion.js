/* Conversion progress tracking via SSE */

(function () {
    const progressSection = document.getElementById('progress-section');
    const stageText = document.getElementById('stage-text');
    const progressBar = document.getElementById('progress-bar');
    const progressDetail = document.getElementById('progress-detail');
    const progressPercent = document.getElementById('progress-percent');
    const resultSection = document.getElementById('result-section');
    const errorSection = document.getElementById('error-section');
    const errorMessage = document.getElementById('error-message');
    const convertSection = document.getElementById('convert-section');
    const previewLink = document.getElementById('preview-link');
    const downloadLink = document.getElementById('download-link');
    const validationSummary = document.getElementById('validation-summary');
    const retryBtn = document.getElementById('retry-btn');

    const stageLabels = {
        'uploaded': 'File uploaded, preparing...',
        'parsing': 'Parsing file content...',
        'splitting': 'Detecting chapters...',
        'extracting_characters': 'Extracting characters...',
        'converting': 'Converting to screenplay...',
        'assembling': 'Assembling screenplay...',
        'validating': 'Validating output...',
        'complete': 'Conversion complete!',
        'error': 'An error occurred',
    };

    window.startProgressTracking = function (jobId) {
        convertSection.classList.add('hidden');
        progressSection.classList.remove('hidden');

        // Use polling instead of SSE for better compatibility
        let polling = true;

        async function poll() {
            if (!polling) return;

            try {
                const resp = await fetch(`/api/status/${jobId}/json`);
                if (!resp.ok) {
                    throw new Error('Failed to get status');
                }

                const status = await resp.json();
                updateProgress(status);

                if (status.stage === 'complete') {
                    polling = false;
                    showResult(jobId);
                    return;
                }

                if (status.stage === 'error') {
                    polling = false;
                    showError(status.error_message || 'Unknown error');
                    return;
                }

                // Continue polling
                setTimeout(poll, 1500);

            } catch (err) {
                polling = false;
                showError(err.message);
            }
        }

        poll();
    };

    function updateProgress(status) {
        const label = stageLabels[status.stage] || status.stage;
        stageText.textContent = label;

        const pct = Math.round(status.progress_percent || 0);
        progressBar.style.width = pct + '%';
        progressPercent.textContent = pct + '%';

        let detail = '';
        if (status.current_chapter && status.total_chapters) {
            detail = `Chapter ${status.current_chapter} of ${status.total_chapters}`;
        } else if (status.total_chapters) {
            detail = `${status.total_chapters} chapters detected`;
        }
        progressDetail.textContent = detail;
    }

    function showResult(jobId) {
        progressSection.classList.add('hidden');
        resultSection.classList.remove('hidden');

        previewLink.href = `/preview/${jobId}`;
        downloadLink.href = `/api/result/${jobId}`;

        // Fetch validation info
        fetch(`/api/validate/${jobId}`)
            .then(r => r.json())
            .then(data => {
                const issues = data.issues || [];
                const errors = issues.filter(i => i.severity === 'error').length;
                const warnings = issues.filter(i => i.severity === 'warning').length;

                if (errors === 0 && warnings === 0) {
                    validationSummary.textContent = 'No validation issues found';
                } else {
                    validationSummary.textContent = `${errors} error(s), ${warnings} warning(s)`;
                }
            })
            .catch(() => {
                validationSummary.textContent = '';
            });
    }

    function showError(message) {
        progressSection.classList.add('hidden');
        errorSection.classList.remove('hidden');
        errorMessage.textContent = message;
    }

    retryBtn.addEventListener('click', () => {
        errorSection.classList.add('hidden');
        convertSection.classList.remove('hidden');
        const convertBtn = document.getElementById('convert-btn');
        convertBtn.disabled = false;
        convertBtn.textContent = 'Start Conversion';
    });
})();
