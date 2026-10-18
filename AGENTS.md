# PixelPilot Agent Guide

PixelPilot is a developer-focused AI website debugging assistant. It accepts a screenshot and optional issue description, console errors, and HTML/CSS context, then requests a structured diagnostic report from Gemma.

## Verified project shape

- Framework and entry point: FastAPI in `app.py`.
- Static frontend: `frontend/index.html` and `frontend/styles.css` (plus the referenced frontend script if present).
- Configuration: `.env.example`; runtime values are read from `GEMINI_API_KEY` and `GEMMA_MODEL`.
- Tests: `tests/test_app.py`, using standard-library `unittest`.
- Required model: `gemma-4-26b-a4b-it`.

Use the project interpreter and install the declared `requirements.txt` dependencies in a controlled environment before running the tests. The focused command is:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_app -v
```

The valid-PNG test isolates the model call; it is not live inference. Only a genuine request using the exact configured model can verify inference.

## Guardrails

- Preserve FastAPI and the current source layout; do not introduce a Streamlit migration or a second backend without approval.
- Never expose `.env` values or API keys, execute uploaded code, fabricate model output, or silently change the model.
- Validate screenshots and model responses, and keep observed screenshot evidence separate from hypotheses.
- Limit edits to the assigned task. Do not commit, push, publish, or deploy without authorization.