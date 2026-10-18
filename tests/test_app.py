import asyncio
import io
import json
import unittest
from unittest.mock import patch

from fastapi import HTTPException, UploadFile
from PIL import Image
from starlette.datastructures import Headers

import app


def make_upload(content: bytes, content_type: str) -> UploadFile:
    return UploadFile(
        file=io.BytesIO(content),
        filename="screenshot.png",
        headers=Headers({"content-type": content_type}),
    )


def make_png() -> bytes:
    image = Image.new("RGB", (2, 2), color="white")
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


class ParseAndValidateJsonTests(unittest.TestCase):
    def test_parses_fenced_json_and_normalizes_issue_defaults(self):
        raw_response = """```json
        {
          "summary": "The layout is clipped.",
          "issues": [{"title": "Clipped panel", "severity": "HIGH"}]
        }
        ```"""

        report = app.parse_and_validate_json(raw_response)

        self.assertEqual(report["summary"], "The layout is clipped.")
        self.assertEqual(report["limitations"], [])
        self.assertEqual(report["issues"], [{
            "title": "Clipped panel",
            "severity": "high",
            "evidence": "Observable from screenshot.",
            "likely_cause": "Hypothesis pending further investigation.",
            "confidence": "medium",
            "next_step": "Inspect element in browser dev tools.",
            "suggested_fix": None,
        }])

    def test_extracts_json_surrounded_by_model_commentary(self):
        report = app.parse_and_validate_json(
            'Here is the report:\n{"summary":"Done","issues":[],"limitations":[]}\n'
        )

        self.assertEqual(report["summary"], "Done")
        self.assertEqual(report["issues"], [])

    def test_returns_none_for_invalid_or_non_object_json(self):
        self.assertIsNone(app.parse_and_validate_json("not json"))
        self.assertIsNone(app.parse_and_validate_json(json.dumps(["not", "an", "object"])))
        self.assertIsNone(app.parse_and_validate_json('{"issues": "not a list"}'))

    def test_fallback_report_preserves_uncertainty_without_fixing_speculation(self):
        report = app.generate_fallback_report("The page looks wrong.", "")

        issue = report["issues"][0]
        self.assertIn("cannot be determined", issue["likely_cause"])
        self.assertIn("computed bounds", issue["next_step"])
        self.assertIsNone(issue["suggested_fix"])

    def test_model_client_uses_configured_timeout(self):
        response = type("Response", (), {"text": '{"summary":"ok","issues":[],"limitations":[]}'} )()
        client = type("Client", (), {
            "models": type("Models", (), {
                "generate_content": lambda self, **kwargs: response,
            })(),
        })()

        with patch("google.genai.Client", return_value=client) as client_factory:
            report = app.call_gemma_analysis("test-key", app.DEFAULT_MODEL, b"png", "image/png")

        self.assertEqual(report["summary"], "ok")
        self.assertEqual(client_factory.call_args.kwargs["http_options"].timeout, app.MODEL_TIMEOUT_MS)

    def test_prompt_requires_evidence_calibrated_hypotheses_and_verification(self):
        response = type("Response", (), {"text": '{"summary":"ok","issues":[],"limitations":[]}'} )()
        with patch("google.genai.Client") as client_factory:
            client_factory.return_value.models.generate_content.return_value = response
            app.call_gemma_analysis(
                "test-key",
                app.DEFAULT_MODEL,
                b"png",
                "image/png",
                user_desc="The page appears blank.",
            )

        prompt = client_factory.return_value.models.generate_content.call_args.kwargs["contents"][0]
        required_guidance = [
            "Report observed symptoms separately from technical explanations",
            "Never infer a JavaScript exception",
            "Severity describes user impact, not diagnostic certainty",
            "Blank or nearly blank screenshot handling",
            "browser Console",
            "Network document, JavaScript, CSS, and API requests",
            "Treat position:absolute, z-index, box-shadow, pseudo-elements, and overflow:hidden as unverified hypotheses",
            "smallest discriminating verification step",
            "request the missing evidence instead of manufacturing certainty",
        ]
        for guidance in required_guidance:
            self.assertIn(guidance, prompt)


class ScreenshotValidationTests(unittest.TestCase):
    def call_analyze(self, upload: UploadFile):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            return asyncio.run(app.analyze_screenshot(upload, "", "", ""))

    def test_rejects_unsupported_mime_type_before_model_call(self):
        with self.assertRaises(HTTPException) as raised:
            self.call_analyze(make_upload(make_png(), "text/plain"))

        self.assertEqual(raised.exception.status_code, 422)
        self.assertIn("Unsupported file type", raised.exception.detail)

    def test_rejects_corrupted_image_with_allowed_mime_type(self):
        with self.assertRaises(HTTPException) as raised:
            self.call_analyze(make_upload(b"not a real image", "image/png"))

        self.assertEqual(raised.exception.status_code, 422)
        self.assertEqual(raised.exception.detail["code"], "invalid_image")

    def test_rejects_image_content_that_does_not_match_mime_type(self):
        with self.assertRaises(HTTPException) as raised:
            self.call_analyze(make_upload(make_png(), "image/jpeg"))

        self.assertEqual(raised.exception.status_code, 422)
        self.assertEqual(raised.exception.detail["code"], "image_content_mismatch")

    def test_rejects_image_over_size_limit_before_integrity_check(self):
        oversized_content = b"0" * (app.MAX_IMAGE_SIZE_BYTES + 1)

        with self.assertRaises(HTTPException) as raised:
            self.call_analyze(make_upload(oversized_content, "image/png"))

        self.assertEqual(raised.exception.status_code, 422)
        self.assertIn("exceeds 10MB limit", raised.exception.detail)

    def test_rejects_overlong_context_instead_of_truncating(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            with self.assertRaises(HTTPException) as raised:
                asyncio.run(app.analyze_screenshot(
                    make_upload(make_png(), "image/png"),
                    "x" * (app.MAX_TEXT_LENGTH + 1),
                    "",
                    "",
                ))

        self.assertEqual(raised.exception.status_code, 422)
        self.assertEqual(raised.exception.detail["code"], "text_too_long")

    def test_rejects_non_required_model_configuration(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key", "GEMMA_MODEL": "other-model"}):
            with self.assertRaises(HTTPException) as raised:
                self.call_analyze(make_upload(make_png(), "image/png"))

        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(raised.exception.detail["code"], "invalid_configuration")

    def test_maps_provider_failures_without_returning_raw_error(self):
        with patch.object(app, "call_gemma_analysis", side_effect=RuntimeError("secret-looking provider detail")):
            with self.assertRaises(HTTPException) as raised:
                self.call_analyze(make_upload(make_png(), "image/png"))

        self.assertEqual(raised.exception.status_code, 502)
        self.assertEqual(raised.exception.detail["code"], "provider_unavailable")
        self.assertNotIn("secret-looking", str(raised.exception.detail))

    def test_http_errors_use_structured_error_envelope(self):
        response = asyncio.run(app.http_exception_handler(
            None,
            HTTPException(status_code=422, detail={"code": "invalid_image"}),
        ))

        self.assertEqual(response.status_code, 422)
        self.assertEqual(json.loads(response.body), {"error": {"code": "invalid_image"}})

    def test_accepts_valid_png_without_live_model_inference(self):
        expected_report = {"summary": "validated", "issues": [], "limitations": []}

        with patch.object(app, "call_gemma_analysis", return_value=expected_report) as model_call:
            response = self.call_analyze(make_upload(make_png(), "image/png"))

        self.assertEqual(json.loads(response.body), expected_report)
        model_call.assert_called_once()
        self.assertEqual(model_call.call_args.kwargs["mime_type"], "image/png")


if __name__ == "__main__":
    unittest.main()