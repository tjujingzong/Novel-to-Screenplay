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
                <p class="text-center py-8 text-red-500">Failed to load samples: ${err.message}</p>
            `;
        }
    }

    function renderSamples() {
        if (currentSamples.length === 0) {
            samplesContainer.innerHTML = `
                <p class="text-center py-8 text-gray-400">No samples available</p>
            `;
            return;
        }

        samplesContainer.innerHTML = currentSamples.map(sample => `
            <div class="border border-gray-200 rounded-lg p-4 hover:border-blue-400 transition-colors">
                <h3 class="font-semibold text-gray-800 mb-2">${escapeHtml(sample.title)}</h3>
                <p class="text-xs text-gray-500 mb-3">${sample.word_count} characters</p>
                <p class="text-sm text-gray-600 mb-4 line-clamp-3" style="display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;">
                    ${escapeHtml(sample.preview.replace(/[#*\n]/g, ' ').substring(0, 120))}...
                </p>
                <div class="flex gap-2">
                    <button class="flex-1 text-xs bg-blue-600 text-white py-1.5 px-3 rounded hover:bg-blue-700 transition-colors use-sample-btn"
                            data-sample-id="${sample.id}">
                        Use This
                    </button>
                    <button class="text-xs text-gray-600 py-1.5 px-3 border border-gray-300 rounded hover:bg-gray-50 transition-colors preview-sample-btn"
                            data-sample-id="${sample.id}">
                        Preview
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
                alert('Sample loaded: ' + sample.title + '\nPlease use the upload area to proceed.');
            }
        } catch (err) {
            alert('Failed to load sample: ' + err.message);
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
            alert('Failed to preview sample: ' + err.message);
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
                <p class="text-center py-8 text-red-500">Failed to load history: ${err.message}</p>
            `;
        }
    }

    function renderHistory(history) {
        if (history.length === 0) {
            historyContainer.innerHTML = `
                <p class="text-center py-8 text-gray-400">No conversion history yet</p>
            `;
            return;
        }

        const stageLabels = {
            'uploaded': 'Uploaded',
            'parsing': 'Parsing',
            'splitting': 'Splitting',
            'extracting_characters': 'Extracting Characters',
            'converting': 'Converting',
            'assembling': 'Assembling',
            'validating': 'Validating',
            'complete': 'Complete',
            'error': 'Error',
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
                                        View
                                    </a>
                                    <a href="/api/result/${item.job_id}" 
                                       class="text-xs text-gray-600 hover:text-gray-800 font-medium">
                                        Download
                                    </a>
                                ` : item.stage === 'error' ? `
                                    <span class="text-xs text-red-500" title="${escapeHtml(item.error_message || 'Unknown error')}">
                                        Error
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
