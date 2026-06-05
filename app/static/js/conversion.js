/* Conversion progress tracking via SSE with streaming output */

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
    const validationIssuesPanel = document.getElementById('validation-issues-panel');
    const validationIssuesList = document.getElementById('validation-issues-list');
    const toggleIssuesBtn = document.getElementById('toggle-issues-btn');
    const issuesChevron = document.getElementById('issues-chevron');
    const retryBtn = document.getElementById('retry-btn');
    const streamOutput = document.getElementById('stream-output');
    const streamText = document.getElementById('stream-text');
    const streamSection = document.getElementById('stream-section');
    const toggleStreamBtn = document.getElementById('toggle-stream');
    let streamBuffer = '';  // Accumulate raw text for markdown rendering

    const stageLabels = {
        'uploaded': '文件已上传，准备中...',
        'parsing': '正在解析文件内容...',
        'splitting': '正在检测章节...',
        'extracting_characters': '正在提取角色信息...',
        'converting': '正在转换为剧本...',
        'assembling': '正在组装剧本...',
        'validating': '正在验证输出...',
        'complete': '转换完成！',
        'error': '发生错误',
    };

    // Toggle validation issues panel
    toggleIssuesBtn.addEventListener('click', () => {
        validationIssuesList.classList.toggle('hidden');
        issuesChevron.classList.toggle('rotate-180');
    });

    // Toggle stream output visibility
    toggleStreamBtn.addEventListener('click', () => {
        streamOutput.classList.toggle('hidden');
    });

    window.startProgressTracking = function (jobId) {
        convertSection.classList.add('hidden');
        progressSection.classList.remove('hidden');
        streamSection.classList.remove('hidden');
        streamBuffer = '';
        streamText.innerHTML = '';

        // Use SSE for real-time streaming
        const eventSource = new EventSource(`/api/status/${jobId}`);

        eventSource.addEventListener('status', (event) => {
            const status = JSON.parse(event.data);
            updateProgress(status);

            if (status.stage === 'complete') {
                eventSource.close();
                showResult(jobId);
            } else if (status.stage === 'error') {
                eventSource.close();
                showError(status.error_message || '未知错误');
            }
        });

        eventSource.addEventListener('chunk', (event) => {
            const data = JSON.parse(event.data);
            if (data.text) {
                streamBuffer += data.text;
                // Render accumulated text as markdown
                streamText.innerHTML = marked.parse(streamBuffer);
                // Auto-scroll to bottom
                streamOutput.scrollTop = streamOutput.scrollHeight;
            }
        });

        eventSource.addEventListener('done', () => {
            eventSource.close();
        });

        eventSource.onerror = () => {
            // Fallback to polling if SSE fails
            eventSource.close();
            startPolling(jobId);
        };
    };

    // Fallback polling method
    function startPolling(jobId) {
        async function poll() {
            try {
                const resp = await fetch(`/api/status/${jobId}/json`);
                if (!resp.ok) throw new Error('获取状态失败');

                const status = await resp.json();
                updateProgress(status);

                if (status.stage === 'complete') {
                    showResult(jobId);
                    return;
                }

                if (status.stage === 'error') {
                    showError(status.error_message || '未知错误');
                    return;
                }

                setTimeout(poll, 1500);
            } catch (err) {
                showError(err.message);
            }
        }
        poll();
    }

    function updateProgress(status) {
        const label = stageLabels[status.stage] || status.stage;
        stageText.textContent = label;

        const pct = Math.round(status.progress_percent || 0);
        progressBar.style.width = pct + '%';
        progressPercent.textContent = pct + '%';

        let detail = '';
        if (status.current_chapter && status.total_chapters) {
            detail = `第 ${status.current_chapter} 章 / 共 ${status.total_chapters} 章`;
        } else if (status.total_chapters) {
            detail = `检测到 ${status.total_chapters} 个章节`;
        }
        progressDetail.textContent = detail;
    }

    function showResult(jobId) {
        progressSection.classList.add('hidden');
        resultSection.classList.remove('hidden');

        // Reset upload button state so user can start a new conversion
        if (window.resetUploadState) {
            window.resetUploadState();
        }

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
                    validationSummary.textContent = '✅ 验证通过，未发现问题';
                    validationIssuesPanel.classList.add('hidden');
                } else if (errors === 0) {
                    validationSummary.textContent = `✅ 生成成功（${warnings} 条提示）`;
                    showValidationIssues(issues);
                } else {
                    validationSummary.textContent = `${errors} 个错误，${warnings} 个警告`;
                    showValidationIssues(issues);
                }
            })
            .catch(() => {
                validationSummary.textContent = '';
            });

        // Refresh history
        if (window.refreshHistory) {
            window.refreshHistory();
        }
    }

    function showValidationIssues(issues) {
        validationIssuesPanel.classList.remove('hidden');

        if (issues.length === 0) {
            validationIssuesList.innerHTML = '<p class="text-sm text-gray-500">无验证问题</p>';
            return;
        }

        const severityIcon = {
            'error': '<span class="inline-block w-2 h-2 rounded-full bg-red-500 mr-2"></span>',
            'warning': '<span class="inline-block w-2 h-2 rounded-full bg-yellow-500 mr-2"></span>',
        };

        let html = '<div class="space-y-2">';
        issues.forEach((issue, idx) => {
            const icon = severityIcon[issue.severity] || severityIcon['warning'];
            html += `
                <div class="flex items-start gap-2 text-sm py-1 border-b border-gray-200 last:border-0">
                    ${icon}
                    <div class="flex-1 min-w-0">
                        <span class="text-gray-700 font-mono text-xs">${issue.path}</span>
                        <p class="text-gray-600 mt-0.5">${issue.message}</p>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        validationIssuesList.innerHTML = html;
    }

    function showError(message) {
        progressSection.classList.add('hidden');
        errorSection.classList.remove('hidden');
        errorMessage.textContent = message;

        // Reset upload button state
        if (window.resetUploadState) {
            window.resetUploadState();
        }
    }

    retryBtn.addEventListener('click', () => {
        errorSection.classList.add('hidden');
        convertSection.classList.remove('hidden');
        const convertBtn = document.getElementById('convert-btn');
        convertBtn.disabled = false;
        convertBtn.textContent = '开始转换';
    });
})();
