# PixelPilot Coding Instructions

## Scope and architecture

- Read `docs/PRD.md`, `docs/ARCHITECTURE.md`, and `docs/IMPLEMENTATION_PLAN.md` before significant changes.
- Preserve the current FastAPI architecture and `app.py` entry point unless an approved plan explicitly changes it.
- Prioritize a working hackathon MVP. Avoid unnecessary dependencies, frameworks, abstractions, and infrastructure.
- Do not redesign the frontend during backend tasks.

## Model integrity

- The mandatory model is `gemma-4-26b-a4b-it`.
- Read the model identifier from `GEMMA_MODEL`; keep that exact default unless an approved requirement changes it.
- Never silently switch models or providers.
- Clearly distinguish mocked responses from genuine inference.
- Never claim live inference succeeded without evidence from a real request.

## Code quality and security

- Validate file types, sizes, image readability, and model responses.
- Never execute uploaded HTML, JavaScript, or other user-provided code.
- Never expose API keys in source, logs, documentation, or Git. Keep `.env` and `.venv/` ignored.
- Handle missing credentials, malformed responses, timeouts, rate limits, quota failures, and network errors.
- Distinguish observed facts from diagnostic hypotheses; never invent evidence, selectors, filenames, or line numbers.
- Update documentation when implementation changes invalidate it.

## Workflow

- Implement one approved task at a time and use targeted tests for the changed behavior.
- Avoid repeated broad audits. Do not mark a phase complete without its acceptance criteria.
- Report blockers instead of silently changing scope.
- Do not commit, push, publish, or deploy without explicit authorization.

## Final reports

Report changed files, implemented requirements, actual checks and results, unresolved blockers, current phase, and next task.