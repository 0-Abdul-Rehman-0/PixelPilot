# PixelPilot Product Requirements

## Overview

PixelPilot helps developers investigate broken or incorrectly rendered websites by combining a screenshot with optional technical context and returning an evidence-grounded debugging report. It is an assistant for investigation, not an autonomous code-fixing system.

## Problem, users, and value

Frontend developers, students, and hackathon judges often have a visible UI symptom but spend time translating it into a testable debugging hypothesis. PixelPilot makes the first diagnostic pass faster by identifying observable symptoms, plausible causes, confidence, and concrete next steps while keeping hypotheses explicit.

The hackathon differentiator is practical multimodal debugging: the required Gemma model receives the visual evidence plus developer-supplied context and returns a structured report rather than a generic chat response.

## Primary journey

1. The developer uploads a PNG, JPEG, or WebP screenshot.
2. They optionally enter an issue description, console errors, and relevant HTML/CSS.
3. PixelPilot validates the input and sends it to the configured exact Gemma model.
4. The developer reviews the structured findings, limitations, and suggested investigation steps.
5. They apply and verify any fix themselves; PixelPilot does not claim autonomous repair.

## Functional requirements

- **FR-001:** Accept PNG, JPEG, and WebP screenshots.
- **FR-002:** Reject unsupported MIME types, unreadable images, and files over 10 MB with actionable errors.
- **FR-003:** Accept optional issue description, console errors, and HTML/CSS context, each bounded at 4000 characters.
- **FR-004:** Send the screenshot and context through the official `google-genai` `generate_content` path using `GEMMA_MODEL`.
- **FR-005:** Default `GEMMA_MODEL` to `gemma-4-26b-a4b-it`; never silently substitute another model.
- **FR-006:** Return a structured report containing summary, issues, limitations, evidence, likely cause, confidence, next step, and optional suggested fix.
- **FR-007:** Parse fenced, commentary-surrounded, and malformed model output safely, using a fallback report when parsing fails.
- **FR-008:** Distinguish observed evidence from hypotheses and state static-analysis limitations.
- **FR-009:** Expose health/configuration status without exposing secrets.

## Non-functional requirements

- **NFR-001:** Never log or return API keys.
- **NFR-002:** Never execute uploaded HTML, CSS, JavaScript, or model-suggested code.
- **NFR-003:** Fail honestly when credentials, quota, model access, or network availability is insufficient.
- **NFR-004:** Keep the MVP proportionate to a solo hackathon project and preserve the current FastAPI architecture.
- **NFR-005:** Provide focused automated coverage for input validation and response parsing.
- **NFR-006:** Keep the workflow usable with keyboard navigation, labels, readable errors, and responsive layout.

## Inputs and outputs

Inputs are one validated screenshot plus optional text context. Output is JSON with `summary`, an `issues` array, and `limitations`. Each issue includes `title`, `severity`, `evidence`, `likely_cause`, `confidence`, `next_step`, and nullable `suggested_fix`.

## Acceptance criteria and user stories

- As a developer, I can upload a supported screenshot and receive a report or a clear provider error.
- As a developer, I can add console errors and HTML/CSS context without those fields being sent beyond their configured length.
- As a reviewer, I can see which statements are visual observations and which are hypotheses.
- As a hackathon judge, I can observe a genuine request using `gemma-4-26b-a4b-it`, provided credentials and model access are available.
- As a maintainer, I can run focused tests without making a live model request.

Acceptance is met when supported images pass validation, invalid files fail before inference, parser tests cover malformed and fenced output, provider failures are surfaced honestly, and a documented live request succeeds or is explicitly recorded as blocked.

## Error states and security

Missing credentials return service-unavailable guidance. Invalid input returns a validation error. Invalid credentials, quota/rate limits, inaccessible models, and other provider failures return distinct API errors without secrets. The service treats HTML/CSS and console text as untrusted context and does not execute it. `.env` and `.venv/` remain ignored.

## Accessibility and usability

The interface should provide labelled upload controls, keyboard access, visible focus, readable status/error text, responsive screenshot preview, and non-color-only severity cues. Reports should remain scannable on small screens.

## MVP scope and exclusions

MVP includes screenshot upload, optional context, genuine Gemma analysis when configured, structured rendering, fallback behavior, exportable report data, and a reproducible broken-page demonstration. Explicitly excluded are autonomous code modification, browser automation, authentication, databases, multi-user SaaS, deployment infrastructure, and claims of verified fixes.

## Risks, assumptions, dependencies, and open questions

The exact model availability and multimodal support depend on the Google API account and current SDK behavior. Model output may be incomplete or speculative, so confidence and limitations are required. Live provider access remains dependent on credentials, quota, network, and model availability. Open questions include whether stricter domain schema validation is needed and how production rate limiting should be configured.

## Success and demonstration

Success means a reproducible screenshot of a broken webpage produces an evidence-grounded, structured report through a genuine request to the exact model, with optional technical context and honest failure handling. The demo should show the broken page, upload and context, model response, proposed investigation, and manual verification of the resulting fix without overstating automation.