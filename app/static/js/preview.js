/* YAML preview page: fetch, highlight, and copy */

(function () {
    const yamlLoading = document.getElementById('yaml-loading');
    const yamlCode = document.getElementById('yaml-code');
    const yamlContent = document.getElementById('yaml-content');
    const copyBtn = document.getElementById('copy-btn');

    async function loadYaml() {
        try {
            const resp = await fetch(`/api/result/${jobId}/text`);
            if (!resp.ok) {
                throw new Error('Failed to load YAML');
            }

            const text = await resp.text();
            yamlContent.textContent = text;
            yamlLoading.classList.add('hidden');
            yamlCode.classList.remove('hidden');

            // Apply syntax highlighting
            hljs.highlightElement(yamlContent);

        } catch (err) {
            yamlLoading.textContent = 'Error loading preview: ' + err.message;
            yamlLoading.classList.add('text-red-500');
        }
    }

    copyBtn.addEventListener('click', async () => {
        try {
            const text = yamlContent.textContent;
            await navigator.clipboard.writeText(text);
            copyBtn.textContent = 'Copied!';
            setTimeout(() => {
                copyBtn.textContent = 'Copy to Clipboard';
            }, 2000);
        } catch (err) {
            alert('Failed to copy: ' + err.message);
        }
    });

    // Load on page ready
    loadYaml();
})();
