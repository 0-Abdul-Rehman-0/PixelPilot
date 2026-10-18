# PixelPilot Implementation Plan

Status values are `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, and `COMPLETE`. Documentation alone does not complete an implementation phase.

## Phase 0 - Repository and documentation baseline

**Status:** COMPLETE

**Objective:** Establish an accurate baseline and executable development workflow.

**Tasks:**

- **P0-001:** Verify source layout, framework, entry point, prompt, parser, and validation path.
- **P0-002:** Create and maintain PRD, architecture, agent instructions, and this plan.
- **P0-003:** Reconcile stale Streamlit README claims with the actual FastAPI application.
- **P0-004:** Repair or recreate a Python environment from `requirements.txt` without changing scope. **Complete:** the repository `.venv` now contains the declared dependencies.
- **P0-005:** Define MVP acceptance criteria and record the test command.

**Deliverables:** Accurate docs, updated setup guidance, executable isolated tests, and a recorded environment status.

**Acceptance and verification:** `app.py` and tests are understood; `GEMMA_MODEL` is documented; `python -m unittest tests.test_app -v` runs in the repaired project environment with 7 tests passing; the app imports successfully; no secrets are exposed.

**Evidence (2026-10-18):** `.venv` was confirmed as the repository interpreter. `fastapi` was the only missing required app import, and `pip install -r requirements.txt` installed it plus its required runtime extras into `.venv` only. The direct route test was corrected to pass explicit optional form values, then the focused suite passed.

**Dependencies/blockers:** Phase 0 environment blocker resolved. The effective local model configuration is now verified separately in the private environment; live inference remains tracked in Phase 1 because no usable API key is configured.

**Definition of done:** Repository structure and known blockers are documented and the test command is reproducible.

## Phase 1 - Model configuration and genuine inference

**Status:** COMPLETE

**Objective:** Verify the exact required model integration.

**Tasks:**

- **P1-001:** Verify `gemma-4-26b-a4b-it` against the official Gemma documentation.
- **P1-002:** Verify SDK initialization, prompt construction, and multimodal request shape.
- **P1-003:** Confirm missing-key, unauthorized, quota, rate, not-found, and network handling.
- **P1-004:** Make one credentialed request with the exact configured model and record evidence or the real blocker.

**Deliverables:** Configuration evidence and a dated live-inference result; no mocked result counts as proof.

**Acceptance/verification:** A genuine request succeeds with the exact model, or the affected phase remains `BLOCKED` with the provider error recorded without secrets.

**Evidence (2026-10-18):** `load_dotenv()` loaded the repository configuration, the effective model matched `gemma-4-26b-a4b-it`, and the configured API key was present. One live text request succeeded with the expected marker. One subsequent live screenshot diagnosis using a generated 2x2 PNG and debugging context returned a structured report with one issue and did not use the fallback report. No secret or raw provider response was printed.

**Dependencies/blockers:** Phase 1 acceptance is satisfied. Future provider failures must still be reported without silently substituting another model.

**Definition of done:** Model identity and live behavior are verified honestly.

## Phase 2 - Reliable input validation

**Status:** COMPLETE

**Objective:** Make screenshot and optional context handling predictable and safe.

**Tasks:**

- **P2-001:** Preserve tests for MIME type, size, image readability, and valid image flow.
- **P2-002:** Verify optional context truncation and safe handling.
- **P2-003:** Add focused cases for any discovered validation regressions.

**Deliverables:** Passing isolated validation tests and clear API errors.

**Acceptance/verification:** Invalid MIME types, mismatched image content, corrupt images, oversized uploads, and overlong context fail before inference; supported images reach the model boundary; no uploaded code executes.

**Evidence (2026-10-18):** Focused tests cover invalid uploads, detected-format mismatch, bounded size reads, overlong context rejection, exact model configuration, and valid PNG routing. Upload filenames are not used for filesystem access.

**Dependencies/blockers:** No known Phase 2 blocker.

**Definition of done:** Focused tests execute and validate the implemented boundary.

## Phase 3 - Structured diagnostic output

**Status:** COMPLETE

**Objective:** Produce stable, evidence-grounded diagnostic reports.

**Tasks:**

- **P3-001:** Test fenced, commentary-surrounded, invalid, and incomplete JSON.
- **P3-002:** Decide whether a strict schema validator is required beyond current normalization.
- **P3-003:** Preserve evidence, hypothesis, confidence, next steps, and limitations in the output contract.

**Deliverables:** Passing parser tests and documented report contract.

**Acceptance/verification:** Malformed output fails safely or falls back; invalid top-level shapes are rejected; observations are not presented as verified causes; provider failures do not expose raw details.

**Evidence (2026-10-18):** Parser tests cover fenced, commentary-surrounded, invalid, non-object, and invalid-shape responses. Provider failure and structured HTTP envelope tests pass. Model calls use a 60-second SDK HTTP timeout. One genuine blank-screenshot analysis with the exact configured model returned a valid report; its causes were marked as hypotheses and its guidance requested verification evidence.

**Dependencies/blockers:** A stricter domain schema remains an optional future enhancement.

**Definition of done:** Parser behavior is covered and its limitations are explicit.

## Phase 4 - Application integration

**Status:** IN PROGRESS

**Objective:** Verify the complete current FastAPI and frontend workflow.

**Tasks:**

- **P4-001:** Run the API with configured credentials in a controlled environment.
- **P4-002:** Exercise upload, context, response rendering, error display, and report export.
- **P4-004 (frontend):** Implemented `frontend/app.js` — upload selection, drag-and-drop, preview with filename/size, replace/remove, client-side validation mirroring backend limits (PNG/JPEG/WebP ≤10 MB), optional description/console/HTML-CSS fields truncated to 4000 chars, `POST /api/analyze` via FormData (exact field names, no manual Content-Type), `GET /api/health` status indicator, loading/duplicate-submission guard, error states preserving user inputs, safe `textContent`-only rendering of the structured report (summary, issues, limitations), copy/download/new-analysis actions.
- **P4-003:** Keep the current framework and avoid introducing a second backend.

**Deliverables:** End-to-end verification notes and any focused fixes.

**Acceptance/verification:** A user can complete the workflow or receives honest, actionable failure feedback.

**Evidence (2026-10-18):** The running FastAPI app resolved the workspace `.env`, reported HTTP 200 health with `gemma-4-26b-a4b-it` and configured credentials, and accepted one real multipart `/api/analyze` request using `screenshot`, `description`, `console_errors`, and `html_css`. The response was HTTP 200 with a valid summary, issues array, and limitations array.

**Dependencies/blockers:** Backend and browser-level integration are verified locally. Production deployment configuration, repository publication, and a skill artifact remain separate submission checks; no mock response was used for the live result.

**Definition of done:** The existing interface is verified against the documented API behavior.

## Phase 5 - Reproducible hackathon demonstration

**Status:** NOT STARTED

**Objective:** Prepare a short, truthful demonstration of multimodal debugging value.

**Tasks:**

- **P5-001:** Prepare a deliberately broken webpage and expected visual symptoms.
- **P5-002:** Supply relevant context and demonstrate genuine Gemma inference.
- **P5-003:** Show the actionable report and manually apply and verify a proposed fix.
- **P5-004:** Explain what Gemma contributed and what remains a developer hypothesis.

**Deliverables:** Demo assets, script, and evidence of the real request.

**Acceptance/verification:** The demo is reproducible and does not present mocks or suggestions as verified automation.

**Dependencies/blockers:** Phases 1 and 4 complete.

**Definition of done:** A judge can see the complete evidence-to-diagnosis workflow.

## Phase 6 - Final acceptance

**Status:** NOT STARTED

**Objective:** Verify and package the MVP.

**Tasks:**

- **P6-001:** Run the focused and final broader test checks once dependencies are available.
- **P6-002:** Verify README setup, model configuration, limitations, and security guidance.
- **P6-003:** Record remaining blockers and acceptance results.

**Deliverables:** Final acceptance report and current documentation.

**Acceptance/verification:** All MVP criteria are checked, live inference status is recorded, and no unsupported capability is claimed.

**Dependencies/blockers:** All prior phases.

**Definition of done:** The repository is ready for a controlled hackathon demonstration.