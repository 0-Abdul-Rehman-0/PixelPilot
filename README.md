# PixelPilot

> AI-powered website debugging assistant for developers, built for Hacktoberfest Hack Day Lahore × Fluxxion Hackathon.
> **Target Award:** Best Use of Gemma 4

PixelPilot takes website screenshots and optional diagnostic context (console errors, code snippets, and an issue description) to produce structured debugging reports with visible evidence, impact severity, calibrated confidence, ranked hypotheses, verification steps, and conditional fix guidance. It is an investigation assistant, not an autonomous code-fixing system.

---

## Features

- 📸 **Multimodal Screenshot Analysis:** Upload PNG, JPEG, or WebP screenshots.
- 🩺 **Diagnostic Context Support:** Pass optional user descriptions, browser console errors, or HTML/CSS snippets.
- 🎯 **Structured Debugging Reports:** JSON outputs with explicit severity badges, evidence, hypotheses, confidence estimates, and next steps.
- 🛡️ **Safety & Validation:** Input validation, structured response normalization, and graceful fallback report handling.
- 📥 **Exportable Findings:** One-click JSON report downloads.
- 🔒 **Safe handling:** Uploaded code is treated as context only; it is never executed, and model output is rendered as text.

---

## Gemma 4 Integration

PixelPilot uses Google's multimodal **Gemma 4** model via the official `google-genai` SDK.

- **SDK:** `google-genai`
- **Required Default Model Identifier:** `gemma-4-26b-a4b-it`
- **API Key Configuration:** `GEMINI_API_KEY` environment variable.

---

## Prerequisites

- **Python:** 3.11+ (Tested on Python 3.14.7)
- **Google AI Studio API key:** Get one from [Google AI Studio](https://aistudio.google.com/apikey).
- **Network access:** Required for live requests to the Google GenAI provider.

---

## Quickstart Guide

### 1. Set Up Environment (Windows PowerShell)

```powershell
# Create local virtual environment
py -m venv .venv

# Activate environment and install dependencies
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Configure API Key

Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and add your Google AI Studio API key:

```env
GEMINI_API_KEY=your_actual_api_key_here
GEMMA_MODEL=gemma-4-26b-a4b-it
```

### 3. Run the Application

```powershell
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

---

## How to Use PixelPilot

1. **Upload Screenshot:** Upload a PNG, JPEG, or WebP image of the buggy website interface.
2. **Add Context (Optional):** Enter a brief issue description, paste browser console errors, or add HTML/CSS snippets.
3. **Analyze:** Click **Analyze Screenshot**.
4. **Inspect Findings:** Review the structured report showing issue title, severity, evidence, hypothesis, and suggested fixes.
5. **Download Report:** Click **Download Structured Report (JSON)** to save the report for your team or issue tracker.

The browser submits multipart fields named exactly `screenshot`, `description`, `console_errors`, and `html_css` to `POST /api/analyze`. The backend validates the image and context, calls `gemma-4-26b-a4b-it`, validates the structured response, and returns `summary`, `issues`, and `limitations`. `GET /api/health` reports readiness and model/configuration status without exposing credentials.

---

## Limitations

- There is no authentication, persistence, multi-user operation, browser automation, autonomous code modification, or feedback/improve-diagnosis workflow.

## Architecture and project structure

`app.py` is the FastAPI entry point and serves both the API and the existing vanilla frontend. It validates uploads and context, constructs the prompt, calls `google.genai.Client(...).models.generate_content(...)`, normalizes the model response, and returns structured JSON. The browser code lives in `frontend/app.js`; markup and styling remain in `frontend/index.html` and `frontend/styles.css`.

```text
app.py                      FastAPI routes, validation, Gemma call, parsing
frontend/index.html         Page markup and /static asset references
frontend/app.js             Upload, health, multipart request, rendering, export
frontend/styles.css         Existing visual styling
tests/test_app.py           Focused unittest coverage
docs/                       PRD, architecture, and implementation evidence
.env.example                Safe configuration template
requirements.txt            Runtime dependencies
LICENSE                     MIT license
```

The main request flow is: browser upload -> `POST /api/analyze` -> MIME, detected-format, size, and text validation -> exact Gemma model -> JSON normalization -> safe text rendering. The model receives `screenshot`, `description`, `console_errors`, and `html_css`.

## Testing and validation

Run checks with the project interpreter:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app -v
.\.venv\Scripts\python.exe -m py_compile app.py tests\test_app.py
node --check frontend\app.js
```

Unit tests cover parser behavior, prompt requirements, uncertainty fallback, upload validation, configuration errors, provider failures, structured errors, and timeout wiring. Tests that isolate the model boundary use mocks and do not count as live inference. A genuine verification requires the exact configured model and a valid private credential.

## Troubleshooting

- **Missing API key:** Create `.env` from `.env.example`, set the key privately, and restart Uvicorn.
- **Invalid model:** Set `GEMMA_MODEL=gemma-4-26b-a4b-it`; the application never silently chooses another model.
- **Invalid upload:** Use a readable PNG, JPEG, or WebP whose content matches its MIME type and is no larger than 10 MB.
- **Context rejected:** Each optional text field is limited to 4000 characters.
- **Provider failure:** Check model access, quota, network, and credentials privately. Browser errors are sanitized.
- **Static asset 404:** Confirm the page references `/static/app.js` and `/static/styles.css` and that Uvicorn is serving this project.
- **Port in use:** Select another local port and open the matching URL.

## Hackathon Submission Compliance

- **Real Gemma 4 integration:** `app.py` uses the official `google-genai` SDK and the required `gemma-4-26b-a4b-it` configuration.
- **Main workflow:** Screenshot, optional context, structured validation, and browser rendering are implemented. A credentialed live text, screenshot, browser diagnosis, and blank-screen diagnosis were verified during development.
- **Diagnostic honesty:** The prompt requires concrete evidence, ranked hypotheses, calibrated confidence/severity, verification steps, and conditional fixes. Unsupported CSS mechanisms are not treated as confirmed causes.
- **Secret handling:** `.env` and `.env.*` are ignored, `.env.example` uses a placeholder, and health/errors do not expose credentials.
- **License:** The repository contains an MIT license.
- **Skill artifact:** [skills/pixelpilot-debugging/SKILL.md](skills/pixelpilot-debugging/SKILL.md) provides the PixelPilot screenshot-diagnosis workflow. No evaluator-specific starter format was present, so this uses conventional `SKILL.md` frontmatter; the external evaluator's exact discovery rules remain unverified.

## Changes from the Original Harness

The repository has no Git commits and contains no separate starter metadata or harness instructions, so a historical diff cannot be verified. The changes verifiable from the current files are the FastAPI entry point, vanilla frontend workflow, Google GenAI integration, screenshot/context validation, structured response normalization, focused tests, agent documentation, and submission documentation. No unverified original feature is claimed.
---

## License

This project is licensed under the [MIT License](LICENSE).
