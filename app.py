"""
PixelPilot — AI Website Debugging Assistant
Backend API (FastAPI)
Built for Hacktoberfest Hack Day Lahore × Fluxxion Hackathon
Target Prize: Best Use of Gemma 4
"""

import os
import json
import logging
import re
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image
import io

load_dotenv()
logger = logging.getLogger("pixelpilot")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_IMAGE_SIZE_MB = 10
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024
MAX_TEXT_LENGTH = 4000
DEFAULT_MODEL = "gemma-4-26b-a4b-it"
MODEL_TIMEOUT_MS = 60_000
ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/webp"}
EXPECTED_IMAGE_FORMATS = {
    "image/png": "PNG",
    "image/jpeg": "JPEG",
    "image/webp": "WEBP",
}

app = FastAPI(title="PixelPilot API", version="1.0.0")


def configured_model() -> str:
    """Return the required model or fail instead of silently substituting one."""
    model = os.getenv("GEMMA_MODEL", DEFAULT_MODEL)
    if model != DEFAULT_MODEL:
        raise ValueError(f"GEMMA_MODEL must be configured as {DEFAULT_MODEL}.")
    return model


def validate_text_field(value: str, field_name: str) -> str:
    if len(value) > MAX_TEXT_LENGTH:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "text_too_long",
                "field": field_name,
                "max_length": MAX_TEXT_LENGTH,
            },
        )
    return value

# ---------------------------------------------------------------------------
# Reusable analysis logic (migrated from Streamlit MVP)
# ---------------------------------------------------------------------------

def parse_and_validate_json(raw_response: str) -> Optional[Dict[str, Any]]:
    """Extract and validate JSON response from the model."""
    if not raw_response:
        return None

    cleaned = raw_response.strip()

    # Strip markdown code blocks (```json ... ``` or ``` ... ```)
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
            except json.JSONDecodeError:
                return None
        else:
            return None

    if not isinstance(data, dict):
        return None

    if not isinstance(data.get("summary", "Analysis completed."), str):
        return None
    if not isinstance(data.get("issues", []), list):
        return None
    if not isinstance(data.get("limitations", []), list):
        return None

    data.setdefault("summary", "Analysis completed.")
    data.setdefault("issues", [])
    data.setdefault("limitations", [])

    validated_issues = []
    for issue in data.get("issues", []):
        if isinstance(issue, dict):
            validated_issues.append({
                "title": str(issue.get("title", "Unclassified Issue")),
                "severity": str(issue.get("severity", "medium")).lower(),
                "evidence": str(issue.get("evidence", "Observable from screenshot.")),
                "likely_cause": str(issue.get("likely_cause", "Hypothesis pending further investigation.")),
                "confidence": str(issue.get("confidence", "medium")).lower(),
                "next_step": str(issue.get("next_step", "Inspect element in browser dev tools.")),
                "suggested_fix": (
                    str(issue["suggested_fix"])
                    if issue.get("suggested_fix") is not None
                    else None
                ),
            })

    data["issues"] = validated_issues
    data["limitations"] = [str(limitation) for limitation in data["limitations"]]
    return data


def generate_fallback_report(user_description: str, console_errors: str) -> Dict[str, Any]:
    """Structured fallback when model returns non-JSON."""
    return {
        "summary": "The available evidence was not sufficient for a reliable structured diagnosis.",
        "issues": [
            {
                "title": "Insufficient diagnostic evidence",
                "severity": "low",
                "evidence": user_description[:200] if user_description else "Screenshot uploaded.",
                "likely_cause": "Hypothesis: The cause cannot be determined from the available screenshot and context.",
                "confidence": "low",
                "next_step": "First provide the relevant DOM or CSS for the affected element; then compare its computed bounds and visibility with the screenshot.",
                "suggested_fix": None,
            }
        ],
        "limitations": [
            "Analysis limited to static visual rendering.",
            "Dynamic state, network responses, and event listeners cannot be fully evaluated from screenshot alone.",
        ],
    }


def call_gemma_analysis(
    api_key: str,
    model_name: str,
    image_bytes: bytes,
    mime_type: str,
    user_desc: str = "",
    console_errors: str = "",
    html_css: str = "",
) -> Dict[str, Any]:
    """Send screenshot + context to Gemma 4 via google-genai SDK."""
    from google import genai
    from google.genai import types

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=MODEL_TIMEOUT_MS),
    )

    prompt = f"""You are PixelPilot, an expert web developer and UI/UX debugging assistant.
Analyze the attached website screenshot alongside any provided diagnostic context.

Return a structured debugging report as **pure JSON only** — no markdown fences, no commentary outside the JSON.

JSON Schema:
{{
  "summary": "Short concise overall diagnosis (1-2 sentences)",
  "issues": [
    {{
      "title": "Short descriptive title of the UI bug",
      "severity": "high | medium | low",
            "evidence": "Concrete details visible in the screenshot or explicitly present in the supplied context; state when evidence is insufficient",
            "likely_cause": "Leading explanation labeled explicitly as a hypothesis, with the reason it fits and important alternatives",
            "confidence": "high | medium | low, based on evidence quality rather than impact",
            "next_step": "Ordered verification action that could confirm or reject the hypothesis and explains what each result would mean",
            "suggested_fix": "Conditional remediation only after verification; use null when the cause is not sufficiently established"
    }}
  ],
  "limitations": [
        "Specific limitation regarding static screenshot analysis",
        "Additional evidence that would resolve the leading uncertainty"
  ]
}}

Reasoning requirements:
- Report observed symptoms separately from technical explanations. Use only visible screenshot evidence and explicitly supplied context.
- Label every unconfirmed cause as a hypothesis. A plausible cause is not a confirmed cause.
- Never infer a JavaScript exception, failed API request, network failure, backend failure, DOM structure, or browser log from a screenshot alone.
- Rank up to three hypotheses by evidential support instead of presenting unrelated possibilities as equally likely.
- Severity describes user impact, not diagnostic certainty. Confidence describes evidence quality.
- Make each next_step specific and ordered: identify the check, the expected evidence, and how it would distinguish the leading hypotheses.
- Use the smallest discriminating verification step first, not a broad audit. For overlap, compare the affected elements' bounds and computed positioning; for a shadow artifact, inspect the computed shadow and pseudo-elements; for clipping, compare the element bounds with its parent overflow and viewport bounds.
- Treat position:absolute, z-index, box-shadow, pseudo-elements, and overflow:hidden as unverified hypotheses unless the supplied context explicitly contains the relevant declaration or diagnostic evidence.
- Do not name a specific CSS property as the cause from pixels alone. Say that a positioning, stacking, shadow, or overflow rule is unverified when CSS was not supplied.
- Do not recommend a specific CSS modification until the relevant cause is supported by supplied context or a verification result; otherwise set suggested_fix to null and request the smallest missing evidence.
- Avoid generic advice such as 'check the console' unless it is tied to the visible symptom and explains what finding would change the diagnosis.

Blank or nearly blank screenshot handling, only when applicable:
- Describe exactly what is visible and say when the screenshot is insufficient to identify a cause.
- Present JavaScript initialization/runtime failure, failed requests, missing or delayed data, CSS visibility/layout/layering, routing/incomplete render, loading/empty/error state, and cropped/incomplete screenshot as ranked hypotheses only when relevant.
- Recommend this evidence sequence as appropriate: browser Console; Network document, JavaScript, CSS, and API requests; DOM presence; CSS visibility, dimensions, positioning, and stacking; then API status and response when data is expected.
- Explain how those checks would confirm or reject each leading hypothesis, and request the missing evidence instead of manufacturing certainty.

User Context:
- Issue Description: {user_desc[:MAX_TEXT_LENGTH] if user_desc else "None provided"}
- Console Errors: {console_errors[:MAX_TEXT_LENGTH] if console_errors else "None provided"}
- HTML/CSS Snippet: {html_css[:MAX_TEXT_LENGTH] if html_css else "None provided"}

Do NOT invent non-existent file names, precise line numbers, exact CSS selectors, DOM nodes, requests, logs, or provider results unless clearly visible in provided code/console text.
Do not claim to have inspected anything beyond the screenshot and supplied context.
Return ONLY valid JSON."""

    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=[prompt, image_part],
        )
        parsed = parse_and_validate_json(response.text)
        if parsed:
            return parsed
        return generate_fallback_report(user_desc, console_errors)

    except Exception as e:
        error_msg = str(e).upper()
        original = str(e)
        if "API_KEY" in error_msg or "UNAUTHORIZED" in error_msg:
            raise ValueError("Invalid or missing API key. Verify your GEMINI_API_KEY.")
        elif "QUOTA" in error_msg or "RATE" in error_msg or "429" in original:
            raise ValueError("API rate limit or quota exceeded. Wait a moment and retry.")
        elif "NOT_FOUND" in error_msg:
            raise ValueError(
                f"Model '{model_name}' is not accessible with this API key. "
                "Verify the model identifier and API key permissions."
            )
        else:
            logger.error("Model API request failed")
            raise RuntimeError("Model API request failed. Retry the request later.") from e


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health_check():
    """Report readiness without exposing secrets."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    try:
        model = configured_model()
        configuration_valid = True
    except ValueError:
        model = None
        configuration_valid = False
    return {
        "status": "ok" if api_key and configuration_valid else "degraded",
        "model": model,
        "api_key_configured": bool(api_key),
        "configuration_valid": configuration_valid,
    }


@app.post("/api/analyze")
async def analyze_screenshot(
    screenshot: UploadFile = File(...),
    description: str = Form(""),
    console_errors: str = Form(""),
    html_css: str = Form(""),
):
    """Accept a screenshot and optional context, return a validated debugging report."""
    # --- Validate API key ---
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not configured. Add it to your .env file and restart the server.",
        )

    # --- Validate file type ---
    content_type = screenshot.content_type or ""
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type: {content_type}. Upload PNG, JPEG, or WebP.",
        )

    # --- Read and validate file size ---
    image_bytes = await screenshot.read(MAX_IMAGE_SIZE_BYTES + 1)
    if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=422,
            detail=f"File size exceeds {MAX_IMAGE_SIZE_MB}MB limit.",
        )

    # --- Validate image integrity ---
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.format != EXPECTED_IMAGE_FORMATS[content_type]:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "image_content_mismatch",
                    "message": "Uploaded image content does not match its MIME type.",
                },
            )
        img.verify()
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_image", "message": "Invalid or corrupted image file."},
        )

    # --- Validate text inputs ---
    description = validate_text_field(description, "description")
    console_errors = validate_text_field(console_errors, "console_errors")
    html_css = validate_text_field(html_css, "html_css")

    # --- Call model ---
    try:
        model_name = configured_model()
    except ValueError as e:
        raise HTTPException(status_code=503, detail={"code": "invalid_configuration", "message": str(e)})
    try:
        report = call_gemma_analysis(
            api_key=api_key,
            model_name=model_name,
            image_bytes=image_bytes,
            mime_type=content_type,
            user_desc=description,
            console_errors=console_errors,
            html_css=html_css,
        )
        return JSONResponse(content=report)
    except ValueError as e:
        raise HTTPException(status_code=502, detail={"code": "provider_rejected_request", "message": str(e)})
    except RuntimeError:
        raise HTTPException(
            status_code=502,
            detail={"code": "provider_unavailable", "message": "The model provider is temporarily unavailable."},
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "request_validation_error", "message": "Invalid request fields."}},
    )


# ---------------------------------------------------------------------------
# Serve frontend (must be last so /api routes take priority)
# ---------------------------------------------------------------------------
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
