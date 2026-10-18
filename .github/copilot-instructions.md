# PixelPilot Copilot Instructions

- Read `AGENTS.md` and the relevant files under `docs/` before substantial work.
- Inspect existing implementations before creating alternatives; preserve the current FastAPI architecture and `app.py` entry point.
- Keep `GEMMA_MODEL` configurable with the exact required default `gemma-4-26b-a4b-it`. Never silently replace the model or provider.
- Use the actual project interpreter and declared dependencies. Do not add FastAPI unless the verified architecture genuinely requires it.
- Never fabricate test results or present mocked responses as live inference.
- Keep changes limited to the assigned files and report blockers honestly.
- Do not commit, push, or deploy without explicit authorization.