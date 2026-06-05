/* Sample novels and history management */

(function () {
    const samplesContainer = document.getElementById('samples-container');
    const historyContainer = document.getElementById('history-container');
    const refreshSamplesBtn = document.getElementById('refresh-samples');
    const refreshHistoryBtn = document.getElementById('refresh-history');

    // Store for sample selection
    let currentSamples = [];

    // ─── Samples ────────────────────────────────────────────────────────────

    async function loadSamples() {
        try {
            const resp = await fetch('/api/samples');
            const data = await resp.json();
            currentSamples = data.samples || [];
            renderSamples();
        } catch (err) {
            samplesContainer.innerHTML = `
                <p class="text-center py-6 text-red-500 text-sm">加载样例失败：${err.message}</p>
            `;
        }
    }

    function renderSamples() {
        if (currentSamples.length === 0) {
            samplesContainer.innerHTML = `
                <p class="text-center py-6 text-gray-400 text-sm">暂无样例</p>
            `;
            return;
        }

        samplesContainer.innerHTML = currentSamples.map(sample => `
            <div class="border border-gray-200 rounded-xl p-3 hover:border-indigo-300 hover:shadow-sm transition-all bg-white">
                <div class="flex items-start justify-between mb-2">
                    <h3 class="font-semibold text-gray-800 text-sm">${escapeHtml(sample.title)}</h3>
                    <span class="text-xs text-gray-400 ml-2 flex-shrink-0">${sample.word_count} 字</span>
                </div>
                <p class="text-xs text-gray-500 mb-3 line-clamp-2" style="display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                    ${escapeHtml(sample.preview.replace(/[#*\n]/g, ' ').substring(0, 100))}
                </p>
                <div class="flex gap-2">
                    <button class="flex-1 text-xs bg-gradient-to-r from-indigo-600 to-blue-600 text-white py-1.5 px-3 rounded-lg hover:from-indigo-700 hover:to-blue-700 transition-all use-sample-btn"
                            data-sample-id="${sample.id}">
                        使用
                    </button>
                    <button class="text-xs text-gray-500 py-1.5 px-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors preview-sample-btn"
                            data-sample-id="${sample.id}">
                        预览
                    </button>
                </div>
            </div>
        `).join('');

        // Add event listeners
        samplesContainer.querySelectorAll('.use-sample-btn').forEach(btn => {
            btn.addEventListener('click', () => useSample(btn.dataset.sampleId));
        });

        samplesContainer.querySelectorAll('.preview-sample-btn').forEach(btn => {
            btn.addEventListener('click', () => previewSample(btn.dataset.sampleId));
        });
    }

    async function useSample(sampleId) {
        try {
            const resp = await fetch(`/api/samples/${sampleId}`);
            const sample = await resp.json();

            // Create a File object from the sample content
            const blob = new Blob([sample.content], { type: 'text/plain' });
            const file = new File([blob], `${sample.title}.txt`, { type: 'text/plain' });

            // Trigger the upload flow
            if (window.handleSampleFile) {
                window.handleSampleFile(file);
            } else {
                alert('已加载样例：' + sample.title + '\n请在上传区域继续操作。');
            }
        } catch (err) {
            alert('加载样例失败：' + err.message);
        }
    }

    async function previewSample(sampleId) {
        try {
            const resp = await fetch(`/api/samples/${sampleId}`);
            const sample = await resp.json();

            // Create a modal or use alert for simplicity
            const modalContent = `
                <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" id="sample-modal">
                    <div class="bg-white rounded-lg p-6 max-w-2xl max-h-[80vh] overflow-auto mx-4">
                        <div class="flex justify-between items-center mb-4">
                            <h3 class="text-lg font-semibold">${escapeHtml(sample.title)}</h3>
                            <button onclick="document.getElementById('sample-modal').remove()" 
                                    class="text-gray-500 hover:text-gray-700">&times;</button>
                        </div>
                        <pre class="whitespace-pre-wrap text-sm text-gray-700">${escapeHtml(sample.content)}</pre>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', modalContent);

            // Close on backdrop click
            document.getElementById('sample-modal').addEventListener('click', (e) => {
                if (e.target.id === 'sample-modal') {
                    e.target.remove();
                }
            });
        } catch (err) {
            alert('预览失败：' + err.message);
        }
    }

    // ─── History ────────────────────────────────────────────────────────────

    async function loadHistory() {
        try {
            const resp = await fetch('/api/history');
            const data = await resp.json();
            renderHistory(data.history || []);
        } catch (err) {
            historyContainer.innerHTML = `
                <p class="text-center py-6 text-red-500 text-sm">加载历史失败：${err.message}</p>
            `;
        }
    }

    function renderHistory(history) {
        if (history.length === 0) {
            historyContainer.innerHTML = `
                <p class="text-center py-6 text-gray-400 text-sm">暂无转换历史</p>
            `;
            return;
        }

        const stageLabels = {
            'uploaded': '已上传',
            'parsing': '解析中',
            'splitting': '分割中',
            'extracting_characters': '提取角色',
            'converting': '转换中',
            'assembling': '组装中',
            'validating': '验证中',
            'complete': '完成',
            'error': '错误',
        };

        const stageColors = {
            'complete': 'text-green-600 bg-green-50',
            'error': 'text-red-600 bg-red-50',
            'converting': 'text-blue-600 bg-blue-50',
        };

        historyContainer.innerHTML = `
            <div class="space-y-3">
                ${history.map(item => {
                    const colorClass = stageColors[item.stage] || 'text-gray-600 bg-gray-50';
                    const stageLabel = stageLabels[item.stage] || item.stage;
                    const timeStr = item.created_at ? new Date(item.created_at).toLocaleString() : 'Unknown';
                    
                    return `
                        <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                            <div class="flex items-center gap-3">
                                <span class="text-xs font-medium px-2 py-1 rounded ${colorClass}">
                                    ${stageLabel}
                                </span>
                                <div>
                                    <p class="font-medium text-gray-800 text-sm">${escapeHtml(item.filename)}</p>
                                    <p class="text-xs text-gray-500">${timeStr}</p>
                                </div>
                            </div>
                            <div class="flex items-center gap-2">
                                ${item.stage === 'complete' ? `
                                    <a href="/preview/${item.job_id}" 
                                       class="text-xs text-blue-600 hover:text-blue-800 font-medium">
                                        查看
                                    </a>
                                    <a href="/api/result/${item.job_id}" 
                                       class="text-xs text-gray-600 hover:text-gray-800 font-medium">
                                        下载
                                    </a>
                                ` : item.stage === 'error' ? `
                                    <span class="text-xs text-red-500" title="${escapeHtml(item.error_message || 'Unknown error')}">
                                        错误
                                    </span>
                                ` : `
                                    <span class="text-xs text-gray-400">
                                        ${Math.round(item.progress_percent || 0)}%
                                    </span>
                                `}
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    // ─── Utilities ──────────────────────────────────────────────────────────

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ─── Event Listeners ────────────────────────────────────────────────────

    refreshSamplesBtn.addEventListener('click', loadSamples);
    refreshHistoryBtn.addEventListener('click', loadHistory);

    // Auto-load on page load
    loadSamples();
    loadHistory();

    // Refresh history periodically (every 5 seconds)
    setInterval(loadHistory, 5000);

    // Export for use in other scripts
    window.refreshHistory = loadHistory;
})();
