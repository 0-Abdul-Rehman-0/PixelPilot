/**
 * PixelPilot — Frontend controller
 * Vanilla JavaScript, no framework. Connects to the FastAPI backend at the
 * same origin:
 *   GET  /api/health   -> service readiness (no secrets exposed)
 *   POST /api/analyze  -> multipart diagnosis request
 *
 * All dynamic model output is inserted via textContent (never innerHTML)
 * to avoid unsafe HTML injection of untrusted AI-generated text.
 */

(function () {
    'use strict';

    // Backend limits (mirror app.py constants so client-side validation matches).
    const ALLOWED_MIME = ['image/png', 'image/jpeg', 'image/webp'];
    const MAX_IMAGE_BYTES = 10 * 1024 * 1024; // 10 MB
    const MAX_TEXT_CHARS = 4000;

    // DOM references
    const $ = (id) => document.getElementById(id);

    const statusDot = $('statusDot');
    const statusText = $('statusText');
    const zone = $('uploadZone');
    const uploadEmpty = $('uploadEmpty');
    const preview = $('uploadPreview');
    const previewImg = $('previewImage');
    const fileMeta = $('fileMeta');
    const removeBtn = $('removeBtn');
    const fileInput = $('fileInput');
    const descriptionField = $('descriptionField');
    const consoleField = $('consoleField');
    const htmlCssField = $('htmlCssField');
    const analyzeBtn = $('analyzeBtn');
    const analyzeBtnLabel = $('analyzeBtnLabel');
    const analyzeBtnLoading = $('analyzeBtnLoading');
    const errorMessage = $('errorMessage');
    const results = $('results');
    const summaryCard = $('summaryCard');
    const issuesList = $('issuesList');
    const limitationsPanel = $('limitationsPanel');
    const limitationsList = $('limitationsList');
    const copyBtn = $('copyBtn');
    const downloadBtn = $('downloadBtn');
    const newAnalysisBtn = $('newAnalysisBtn');

    let currentUrl = null;   // active object URL for preview
    let selectedFile = null;  // retained after clearing the native input value
    let lastReport = null;   // latest parsed report (for copy/download)
    let analyzing = false;   // duplicate-submission guard

    // ------------------------------------------------------------------
    // Helpers
    // ------------------------------------------------------------------
    function fmtBytes(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / 1024 / 1024).toFixed(2) + ' MB';
    }

    function setError(msg) {
        errorMessage.textContent = msg || '';
        errorMessage.hidden = !msg;
    }

    function hideResults() {
        results.hidden = true;
        summaryCard.textContent = '';
        issuesList.textContent = '';
        limitationsPanel.hidden = true;
        limitationsList.textContent = '';
        lastReport = null;
    }

    function setLoading(isLoading) {
        analyzing = isLoading;
        analyzeBtn.disabled = isLoading;
        analyzeBtnLoading.hidden = !isLoading;
        analyzeBtnLabel.textContent = isLoading ? 'Analyzing…' : 'Analyze screenshot';
        analyzeBtn.setAttribute('aria-busy', String(isLoading));
        if (isLoading) {
            setError('');
            hideResults();
        }
    }

    function revokeCurrent() {
        if (currentUrl) {
            URL.revokeObjectURL(currentUrl);
            currentUrl = null;
        }
    }

    function updateStatusIndicator(state, label) {
        statusDot.className = 'status-dot';
        if (state === 'ready') {
            statusDot.classList.add('ready');
            statusText.textContent = label || 'Ready';
        } else if (state === 'no-key') {
            statusDot.classList.add('no-key');
            statusText.textContent = label || 'Gemma key not configured';
        } else if (state === 'error') {
            statusDot.classList.add('error');
            statusText.textContent = label || 'Service unreachable';
        } else {
            statusText.textContent = label || 'Checking…';
        }
    }

    // ------------------------------------------------------------------
    // Health check (truthful, never exposes credentials)
    // ------------------------------------------------------------------
    async function runHealthCheck() {
        updateStatusIndicator(null, 'Checking…');
        try {
            const resp = await fetch('/api/health');
            if (resp.ok) {
                const data = await resp.json();
                if (data.status === 'ok' && data.api_key_configured && data.configuration_valid !== false) {
                    updateStatusIndicator('ready', 'Ready (' + (data.model || 'gemma') + ')');
                } else if (data.configuration_valid === false) {
                    updateStatusIndicator('error', 'Backend configuration invalid');
                } else {
                    updateStatusIndicator('no-key', 'Gemma key not configured');
                }
            } else {
                updateStatusIndicator('error', 'Service error');
            }
        } catch (err) {
            updateStatusIndicator('error', 'Unable to reach service');
        }
    }

    // ------------------------------------------------------------------
    // Upload / preview / validation
    // ------------------------------------------------------------------
    function validateFile(file) {
        if (!ALLOWED_MIME.includes(file.type)) {
            return 'Unsupported file type: ' + (file.type || 'unknown').replace(/^image\//, '') + '. Upload PNG, JPEG, or WebP.';
        }
        if (file.size > MAX_IMAGE_BYTES) {
            return 'File size exceeds 10 MB limit.';
        }
        return null;
    }

    function applyFile(file) {
        revokeCurrent();
        currentUrl = URL.createObjectURL(file);
        previewImg.src = currentUrl;
        previewImg.alt = 'Screenshot preview: ' + file.name;
        fileMeta.textContent = file.name + '  ·  ' + fmtBytes(file.size);
        fileMeta.hidden = false;
        preview.hidden = false;
        uploadEmpty.hidden = true;
        setError('');
    }

    function clearSelection() {
        revokeCurrent();
        selectedFile = null;
        previewImg.src = '';
        previewImg.alt = '';
        preview.hidden = true;
        uploadEmpty.hidden = false;
        fileMeta.hidden = true;
        fileMeta.textContent = '';
        fileInput.value = '';
        analyzeBtn.disabled = true;
        analyzeBtnLoading.hidden = true;
        analyzeBtnLabel.textContent = 'Analyze screenshot';
        hideResults();
        setError('');
    }

    function handleFile(file) {
        const err = validateFile(file);
        if (err) {
            selectedFile = null;
            setError(err);
            revokeCurrent();
            preview.hidden = true;
            uploadEmpty.hidden = false;
            fileMeta.hidden = true;
            analyzeBtn.disabled = true;
            return;
        }
        selectedFile = file;
        applyFile(file);
        analyzeBtn.disabled = false;
    }

    zone.addEventListener('click', () => fileInput.click());

    zone.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            fileInput.click();
        }
    });

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files && e.target.files[0];
        if (file) handleFile(file);
        e.target.value = ''; // allow re-selecting the same file
    });

    removeBtn.addEventListener('click', (event) => {
        event.stopPropagation();
        clearSelection();
    });

    // Drag-and-drop
    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('dragover');
    });
    zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('dragover');
        const file = e.dataTransfer && e.dataTransfer.files[0];
        if (file) handleFile(file);
    });

    // Truncate optional text fields client-side to match backend limit.
    [descriptionField, consoleField, htmlCssField].forEach((field) => {
        field.addEventListener('input', () => {
            if (field.value.length > MAX_TEXT_CHARS) {
                field.value = field.value.slice(0, MAX_TEXT_CHARS);
            }
        });
    });

    // ------------------------------------------------------------------
    // Diagnosis submission -> POST /api/analyze (multipart FormData)
    // ------------------------------------------------------------------
    async function runDiagnosis() {
        if (analyzing) return;

        const file = selectedFile;
        if (!file) {
            setError('Please select a screenshot before analyzing.');
            return;
        }
        const err = validateFile(file);
        if (err) {
            setError(err);
            return;
        }

        const formData = new FormData();
        formData.append('screenshot', file, file.name);
        formData.append('description', descriptionField.value || '');
        formData.append('console_errors', consoleField.value || '');
        formData.append('html_css', htmlCssField.value || '');

        setLoading(true);

        try {
            const resp = await fetch('/api/analyze', {
                method: 'POST',
                body: formData,
                // Do NOT set Content-Type: the browser sets the multipart boundary automatically.
            });

            let detail = null;
            let report = null;
            try {
                const payload = await resp.json();
                if (resp.ok && payload && typeof payload === 'object' &&
                    typeof payload.summary === 'string' &&
                    Array.isArray(payload.issues) &&
                    Array.isArray(payload.limitations)) {
                    report = payload;
                } else {
                    const error = payload && (payload.error || payload.detail);
                    if (typeof error === 'string') {
                        detail = error;
                    } else if (error && typeof error === 'object' && error.message) {
                        detail = String(error.message);
                    } else if (error && typeof error === 'object' && error.code) {
                        detail = 'Request failed: ' + String(error.code);
                    } else {
                        detail = 'Server returned an unexpected response.';
                    }
                }
            } catch (e) {
                detail = 'Could not parse server response.';
            }

            if (report) {
                lastReport = report;
                renderResults(report);
                results.hidden = false;
                setLoading(false);
            } else {
                setError((resp.status === 503 ? 'Backend unavailable: ' : '') +
                         (detail || 'Analysis failed (' + resp.status + ').'));
                setLoading(false);
            }
        } catch (e) {
            setError('Network error — unable to reach the backend.');
            setLoading(false);
        }
    }

    analyzeBtn.addEventListener('click', runDiagnosis);

    // ------------------------------------------------------------------
    // Safe result rendering (textContent only — no innerHTML)
    // ------------------------------------------------------------------
    function createIssueField(label, value) {
        const div = document.createElement('div');
        div.className = 'issue-field';
        const strong = document.createElement('strong');
        strong.className = 'issue-field-label';
        strong.textContent = label + ':';
        const span = document.createElement('span');
        span.className = 'issue-field-value';
        span.textContent = value === null || value === undefined ? 'None provided' : String(value);
        div.appendChild(strong);
        div.appendChild(span);
        return div;
    }

    function renderResults(report) {
        // Summary
        if (report.summary) {
            const h = document.createElement('h3');
            h.textContent = 'Summary';
            h.style.marginBottom = '0.35rem';
            const p = document.createElement('p');
            p.textContent = report.summary;
            summaryCard.appendChild(h);
            summaryCard.appendChild(p);
        }

        // Issues
        const issues = report.issues || [];
        if (issues.length) {
            const h = document.createElement('h3');
            h.textContent = 'Identified Issues';
            h.style.margin = '1rem 0 0.5rem';
            issuesList.appendChild(h);
            issues.forEach((issue) => {
                const card = document.createElement('div');
                card.className = 'issue-card';
                card.setAttribute('data-severity', issue.severity || 'medium');

                const header = document.createElement('div');
                header.className = 'issue-card-header';

                const title = document.createElement('strong');
                title.className = 'issue-title';
                title.textContent = issue.title || 'Unclassified Issue';
                header.appendChild(title);

                const badge = document.createElement('span');
                badge.className = 'severity-badge';
                badge.setAttribute('data-severity', issue.severity || 'medium');
                badge.textContent = String(issue.severity || 'medium').toUpperCase();
                header.appendChild(badge);

                const confidence = document.createElement('span');
                confidence.className = 'confidence-tag';
                confidence.textContent = 'Confidence: ' + String(issue.confidence || 'medium');
                header.appendChild(confidence);

                card.appendChild(header);

                card.appendChild(createIssueField('Evidence', issue.evidence));
                card.appendChild(createIssueField('Likely cause (hypothesis)', issue.likely_cause));
                card.appendChild(createIssueField('Next step', issue.next_step));

                if (issue.suggested_fix) {
                    const fixWrap = document.createElement('div');
                    fixWrap.style.marginTop = '0.5rem';
                    const fixLabel = document.createElement('strong');
                    fixLabel.textContent = 'Suggested fix:';
                    fixLabel.style.display = 'block';
                    fixLabel.style.marginBottom = '0.25rem';
                    fixLabel.style.fontSize = '0.8rem';
                    fixLabel.style.color = 'var(--text-secondary)';
                    fixWrap.appendChild(fixLabel);
                    const fixBox = document.createElement('pre');
                    fixBox.className = 'suggested-fix';
                    fixBox.textContent = String(issue.suggested_fix);
                    fixWrap.appendChild(fixBox);
                    card.appendChild(fixWrap);
                }

                issuesList.appendChild(card);
            });
        } else {
            const note = document.createElement('p');
            note.textContent = 'No issues were identified by the model during this pass.';
            note.style.fontStyle = 'italic';
            note.style.color = 'var(--text-secondary)';
            issuesList.appendChild(note);
        }

        // Limitations
        const limitations = report.limitations || [];
        if (limitations.length) {
            limitations.forEach((item) => {
                const li = document.createElement('li');
                li.textContent = item;
                limitationsList.appendChild(li);
            });
        }
    }

    // ------------------------------------------------------------------
    // Report actions: copy JSON, download JSON, new analysis
    // ------------------------------------------------------------------
    copyBtn.addEventListener('click', async () => {
        if (!lastReport) return;
        const json = JSON.stringify(lastReport, null, 2);
        try {
            await navigator.clipboard.writeText(json);
            const oldLabel = copyBtn.textContent;
            copyBtn.textContent = 'Copied!';
            setTimeout(() => { copyBtn.textContent = oldLabel; }, 1600);
        } catch (e) {
            // Fallback: select-and-copy via textarea
            const ta = document.createElement('textarea');
            ta.textContent = json;
            ta.style.position = 'fixed';
            ta.style.opacity = '0';
            document.body.appendChild(ta);
            ta.select();
            try { document.execCommand('copy'); } catch (e2) {}
            document.body.removeChild(ta);
            const oldLabel = copyBtn.textContent;
            copyBtn.textContent = 'Copied!';
            setTimeout(() => { copyBtn.textContent = oldLabel; }, 1600);
        }
    });

    downloadBtn.addEventListener('click', () => {
        if (!lastReport) return;
        const json = JSON.stringify(lastReport, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'pixelpilot-report.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });

    newAnalysisBtn.addEventListener('click', clearSelection);

    // ------------------------------------------------------------------
    // Init
    // ------------------------------------------------------------------
    analyzeBtn.disabled = true;
    runHealthCheck();
})();
