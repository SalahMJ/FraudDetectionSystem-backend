from __future__ import annotations
import httpx
from typing import Any, Dict, Optional
from app.config import get_settings

SYSTEM_INSTRUCTIONS = (
    "You are an analytics assistant for a fraud detection dashboard. "
    "Given JSON stats (totals and daily time series), produce: \n"
    "1) A concise natural-language insight (2-5 sentences).\n"
    "2) Optionally, a chart spec matching the user's intent. Prefer Apache ECharts option JSON when the user asks for common chart types (bar/line/pie). "
    "If you output Vega-Lite v5 instead, ensure $schema is included.\n"
    "If no chart is useful, set chartSpec to null.\n"
    "Respond strictly as JSON with keys: insight (string), chartSpec (object|null), chartType (string|null).\n"
    "Set chartType to 'echarts' for ECharts option JSON, or 'vega-lite' for Vega-Lite."
)


def call_gemini(prompt: str, stats_json: Dict[str, Any]) -> Dict[str, Any]:
    settings = get_settings()
    api_key = settings.GEMINI_API_KEY or ""
    model = settings.GEMINI_MODEL or "gemini-2.5-flash"
    generation_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    if not api_key:
        # Fallback: no key configured
        return {
            "insight": "Gemini API key not configured. Set GEMINI_API_KEY to enable AI insights.",
            "chartSpec": None,
        }

    headers = {"Content-Type": "application/json"}
    params = {"key": api_key}
    # Compose content for Gemini
    user_content = (
        f"System Instructions:\n{SYSTEM_INSTRUCTIONS}\n\n"
        f"User Prompt:\n{prompt}\n\n"
        f"Stats JSON (use this as data):\n{stats_json}\n"
    )
    payload = {
        "contents": [
            {"parts": [{"text": user_content}]}
        ]
    }

    try:
        with httpx.Client(timeout=30) as client:
            r = client.post(generation_url, headers=headers, params=params, json=payload)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        return {"insight": f"AI service call failed: {e}", "chartSpec": None}

    # Parse a simple text response; Gemini may return candidates[].content.parts[].text
    text: Optional[str] = None
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        text = None

    # Try to extract JSON block if the model returned raw JSON
    import json, re
    if text:
        # 1) fenced JSON ```json ... ```
        m = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
        if m:
            try:
                parsed = json.loads(m.group(1))
                if isinstance(parsed, dict):
                    return {
                        "insight": parsed.get("insight") or "",
                        "chartSpec": parsed.get("chartSpec"),
                        "chartType": parsed.get("chartType"),
                    }
            except Exception:
                pass
        # 2) direct JSON object
        text_stripped = text.strip()
        if text_stripped.startswith('{') and text_stripped.endswith('}'):
            try:
                parsed = json.loads(text_stripped)
                if isinstance(parsed, dict):
                    return {
                        "insight": parsed.get("insight") or text_stripped,
                        "chartSpec": parsed.get("chartSpec"),
                        "chartType": parsed.get("chartType"),
                    }
            except Exception:
                pass

    # Fallback: return raw text as insight
    return {"insight": (text or "No insight returned.").strip(), "chartSpec": None, "chartType": None}
