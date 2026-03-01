from __future__ import annotations
import json


def parse_ai_response(raw: str) -> dict:
    """
    Parse AI response to JSON.
    Handles: markdown fences, truncated JSON, empty responses.
    Raises ValueError with a clear message if parsing fails.
    """
    raw = raw.strip()

    # Strip markdown code fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    # Guard against empty
    if not raw or raw == "{":
        raise ValueError("AI returned an empty response.")

    # Direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Fallback: trim to last valid closing brace
    last_brace = raw.rfind("}")
    if last_brace != -1:
        try:
            return json.loads(raw[:last_brace + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse AI response as JSON. First 200 chars: {raw[:200]}")