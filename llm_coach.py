import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

_client = None

def _get_model():
    global _client
    if _client is None:
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            raise RuntimeError(
                "GEMINI_API_KEY not set. Add it to .env:\n"
                "  echo 'GEMINI_API_KEY=AIzaSy...' > .env"
            )
        _client = genai.Client(api_key=key)
    return _client

TRIGGER_DESCRIPTIONS = {
    "POSTURE_NUDGE":   "the user has been slouching for more than 70% of the last 30 seconds",
    "EARLY_BREAK":     "the user's focus has dropped significantly — triggering an early break",
    "FLOW_EXTENSION":  "the user is in a deep flow state — extending the work session by 5 minutes",
    "SESSION_END":     "the user just completed a full study session",
    "PHONE_DETECTED":  "the user's hand is visible and their gaze is away from the screen — likely on their phone during a work block",
}

FALLBACKS = {
    "POSTURE_NUDGE":  "You've been slouching — sit up straight and take a breath!",
    "EARLY_BREAK":    "Your focus has dipped. Take a short break — you've earned it.",
    "FLOW_EXTENSION": "You're in the zone! Extending your session by 5 minutes.",
    "SESSION_END":    "Great session! Take a moment to review what you accomplished.",
    "PHONE_DETECTED": "Put the phone down — you're in a work block. Refocus!",
}

MODEL = "models/gemini-2.5-flash-lite"

def get_coaching_message(trigger: str, context: dict) -> str:
    focus      = context.get("focus_score", 50)
    elapsed    = context.get("elapsed_mins", 0)
    noise      = context.get("noise_level_db", 40)
    app        = context.get("top_app", "Unknown")
    blink_rate = context.get("blink_rate_per_min", 15)

    description = TRIGGER_DESCRIPTIONS.get(trigger, f"a {trigger} event occurred")

    prompt = f"""You are a concise study coach in a focus tracking app.
Event: {description}.

Context: focus={focus:.0f}%, elapsed={elapsed:.0f}min, noise={noise:.0f}dB, app={app}, blinks={blink_rate:.0f}/min (normal 15-20).

Reply with EXACTLY 2-3 bullet points using • as the bullet character. Each bullet is one short sentence (max 12 words). Be specific, warm, and actionable. No intro text, no markdown formatting, bullets only."""

    try:
        client = _get_model()
        response = client.models.generate_content(model=MODEL, contents=prompt)
        return response.text.strip()
    except Exception:
        return FALLBACKS.get(trigger, "Keep going — you're doing great!")
