/* Editor page: YAML editing (CodeMirror), AI suggestions, screenplay generation (Markdown) */

(function () {
    // ─── Tab Management ─────────────────────────────────────────────────────

    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            tabBtns.forEach(b => {
                b.classList.remove('active', 'border-b-2', 'border-indigo-600', 'text-indigo-600', 'bg-white');
                b.classList.add('text-gray-500');
            });
            btn.classList.add('active', 'border-b-2', 'border-indigo-600', 'text-indigo-600', 'bg-white');
            btn.classList.remove('text-gray-500');
            tabContents.forEach(c => c.classList.add('hidden'));
            document.getElementById(`tab-${tabName}`).classList.remove('hidden');
            // Refresh CodeMirror when switching to YAML tab
            if (tabName === 'yaml-edit' && window._yamlCM) {
                setTimeout(() => window._yamlCM.refresh(), 10);
            }
        });
    });

    // ─── CodeMirror YAML Editor ─────────────────────────────────────────────

    const yamlCMContainer = document.getElementById('yaml-cm-editor');
    const yamlSaveBtn = document.getElementById('yaml-save-btn');
    const yamlSaveStatus = document.getElementById('yaml-save-status');

    // Initialize CodeMirror
    const yamlCM = CodeMirror(yamlCMContainer, {
        value: '# 加载中...',
        mode: 'yaml',
        theme: 'dracula',
        lineNumbers: true,
        lineWrapping: true,
        indentUnit: 2,
        tabSize: 2,
        matchBrackets: true,
        autoCloseBrackets: true,
    });
    window._yamlCM = yamlCM;

    // Helper: get YAML text from CodeMirror
    function getYamlText() {
        return yamlCM.getValue();
    }

    // Helper: set YAML text into CodeMirror
    function setYamlText(text) {
        yamlCM.setValue(text);
    }

    // Load YAML content
    async function loadYaml() {
        try {
            const resp = await fetch(`/api/result/${jobId}/text`);
            if (!resp.ok) throw new Error('加载 YAML 失败');
            const text = await resp.text();
            setYamlText(text);
        } catch (err) {
            setYamlText(`# 加载失败: ${err.message}`);
        }
    }

    // Save YAML
    yamlSaveBtn.addEventListener('click', async () => {
        yamlSaveBtn.disabled = true;
        yamlSaveBtn.textContent = '保存中...';

        try {
            const resp = await fetch(`/api/yaml/${jobId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ yaml_content: getYamlText() }),
            });

            if (!resp.ok) {
                const err = await resp.json();
                throw new Error(err.detail || '保存失败');
            }

            yamlSaveStatus.classList.remove('hidden');
            setTimeout(() => yamlSaveStatus.classList.add('hidden'), 2000);

        } catch (err) {
            alert('保存失败: ' + err.message);
        } finally {
            yamlSaveBtn.disabled = false;
            yamlSaveBtn.textContent = '保存修改';
        }
    });

    // ─── Markdown Rendering Helper ──────────────────────────────────────────

    function renderMarkdown(container, text) {
        container.innerHTML = marked.parse(text);
    }

    // ─── Regeneration with Suggestions ──────────────────────────────────────

    const suggestionsInput = document.getElementById('suggestions-input');
    const regenerateBtn = document.getElementById('regenerate-btn');
    const regenStatus = document.getElementById('regen-status');
    const regenOutputContainer = document.getElementById('regen-output-container');
    const regenTextEl = document.getElementById('regen-text');
    const applyRegenBtn = document.getElementById('apply-regen-btn');

    let regeneratedYaml = '';

    regenerateBtn.addEventListener('click', async () => {
        const suggestions = suggestionsInput.value.trim();
        if (!suggestions) {
            alert('请输入修改建议');
            return;
        }

        regenerateBtn.disabled = true;
        regenerateBtn.textContent = '生成中...';
        regenStatus.textContent = '正在调用 AI 重新生成...';
        regenOutputContainer.classList.remove('hidden');
        regenTextEl.innerHTML = '';
        regeneratedYaml = '';
        applyRegenBtn.classList.add('hidden');

        try {
            const apiKey = localStorage.getItem('deepseek_api_key') || '';

            const resp = await fetch(`/api/regenerate/${jobId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ suggestions, api_key: apiKey }),
            });

            if (!resp.ok) {
                const err = await resp.json();
                throw new Error(err.detail || '重新生成失败');
            }

            const reader = resp.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.text) {
                                regeneratedYaml += data.text;
                                renderMarkdown(regenTextEl, regeneratedYaml);
                                const output = document.getElementById('regen-output');
                                output.scrollTop = output.scrollHeight;
                            }
                        } catch (e) { /* skip */ }
                    } else if (line.startsWith('event: done')) {
                        regenStatus.textContent = '生成完成！';
                        applyRegenBtn.classList.remove('hidden');
                    }
                }
            }

            regenStatus.textContent = '生成完成！';
            applyRegenBtn.classList.remove('hidden');

        } catch (err) {
            regenStatus.textContent = '错误: ' + err.message;
        } finally {
            regenerateBtn.disabled = false;
            regenerateBtn.textContent = 'AI 重新生成';
        }
    });

    // Apply regenerated YAML
    applyRegenBtn.addEventListener('click', () => {
        if (regeneratedYaml) {
            setYamlText(regeneratedYaml);
            yamlSaveBtn.click();
            tabBtns[0].click();
            regenStatus.textContent = '已应用到 YAML 编辑器';
        }
    });

    // ─── Screenplay Generation ──────────────────────────────────────────────

    const convertScreenplayBtn = document.getElementById('convert-screenplay-btn');
    const screenplayToggleEditBtn = document.getElementById('screenplay-toggle-edit');
    const screenplayStatus = document.getElementById('screenplay-status');
    const screenplayPreview = document.getElementById('screenplay-preview');
    const screenplayRendered = document.getElementById('screenplay-rendered');
    const screenplayEditorWrap = document.getElementById('screenplay-editor-wrap');
    const screenplayEditor = document.getElementById('screenplay-editor');
    const screenplayStream = document.getElementById('screenplay-stream');
    const screenplayStreamTextEl = document.getElementById('screenplay-stream-text');
    const screenplaySaveBtn = document.getElementById('screenplay-save-btn');
    const screenplayDownloadBtn = document.getElementById('screenplay-download-btn');

    let screenplayContent = '';
    let isEditingScreenplay = false;

    // Toggle preview/edit mode
    screenplayToggleEditBtn.addEventListener('click', () => {
        isEditingScreenplay = !isEditingScreenplay;
        if (isEditingScreenplay) {
            screenplayPreview.classList.add('hidden');
            screenplayEditorWrap.classList.remove('hidden');
            screenplayEditor.value = screenplayContent;
            screenplayToggleEditBtn.textContent = '预览渲染';
        } else {
            screenplayEditorWrap.classList.add('hidden');
            screenplayPreview.classList.remove('hidden');
            screenplayContent = screenplayEditor.value;
            renderMarkdown(screenplayRendered, screenplayContent);
            screenplayToggleEditBtn.textContent = '编辑源码';
        }
    });

    // Load existing screenplay
    async function loadScreenplay() {
        try {
            const resp = await fetch(`/api/screenplay/${jobId}`);
            if (resp.ok) {
                const data = await resp.json();
                if (data.content) {
                    screenplayContent = data.content;
                    renderMarkdown(screenplayRendered, screenplayContent);
                    screenplayPreview.classList.remove('hidden');
                    screenplayToggleEditBtn.classList.remove('hidden');
                    screenplaySaveBtn.classList.remove('hidden');
                    screenplayDownloadBtn.classList.remove('hidden');
                    return true;
                }
            }
        } catch (e) { /* no existing screenplay */ }
        return false;
    }

    convertScreenplayBtn.addEventListener('click', async () => {
        convertScreenplayBtn.disabled = true;
        convertScreenplayBtn.textContent = '生成中...';
        screenplayStatus.classList.remove('hidden');
        screenplayStream.classList.remove('hidden');
        screenplayPreview.classList.add('hidden');
        screenplayEditorWrap.classList.add('hidden');
        screenplayStreamTextEl.innerHTML = '';
        screenplayContent = '';

        try {
            const apiKey = localStorage.getItem('deepseek_api_key') || '';

            const resp = await fetch(`/api/screenplay/${jobId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ suggestions: '', api_key: apiKey }),
            });

            if (!resp.ok) {
                const err = await resp.json();
                throw new Error(err.detail || '生成剧本失败');
            }

            const reader = resp.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.text) {
                                screenplayContent += data.text;
                                renderMarkdown(screenplayStreamTextEl, screenplayContent);
                                const stream = document.getElementById('screenplay-stream');
                                stream.scrollTop = stream.scrollHeight;
                            }
                        } catch (e) { /* skip */ }
                    } else if (line.startsWith('event: done')) {
                        // done
                    }
                }
            }

            // Show rendered screenplay
            screenplayStatus.classList.add('hidden');
            screenplayStream.classList.add('hidden');
            screenplayPreview.classList.remove('hidden');
            screenplayToggleEditBtn.classList.remove('hidden');
            screenplaySaveBtn.classList.remove('hidden');
            screenplayDownloadBtn.classList.remove('hidden');
            renderMarkdown(screenplayRendered, screenplayContent);
            isEditingScreenplay = false;
            screenplayToggleEditBtn.textContent = '编辑源码';

        } catch (err) {
            screenplayStatus.classList.add('hidden');
            screenplayStream.classList.add('hidden');
            alert('生成剧本失败: ' + err.message);
        } finally {
            convertScreenplayBtn.disabled = false;
            convertScreenplayBtn.textContent = '生成正式剧本';
        }
    });

    // Save screenplay
    screenplaySaveBtn.addEventListener('click', async () => {
        screenplaySaveBtn.disabled = true;
        screenplaySaveBtn.textContent = '保存中...';

        // If editing, grab latest content
        if (isEditingScreenplay) {
            screenplayContent = screenplayEditor.value;
        }

        try {
            const resp = await fetch(`/api/screenplay/${jobId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ screenplay_content: screenplayContent }),
            });

            if (!resp.ok) {
                const err = await resp.json();
                throw new Error(err.detail || '保存失败');
            }

            screenplaySaveBtn.textContent = '已保存！';
            setTimeout(() => { screenplaySaveBtn.textContent = '保存修改'; }, 2000);

        } catch (err) {
            alert('保存失败: ' + err.message);
        } finally {
            screenplaySaveBtn.disabled = false;
        }
    });

    // Download screenplay
    screenplayDownloadBtn.addEventListener('click', () => {
        window.location.href = `/api/screenplay/${jobId}/download`;
    });

    // ─── Initialize ─────────────────────────────────────────────────────────

    // Load API key from localStorage
    const cachedKey = localStorage.getItem('deepseek_api_key');
    if (cachedKey) {
        sessionStorage.setItem('api_key', cachedKey);
    }

    loadYaml();
    loadScreenplay();

})();
