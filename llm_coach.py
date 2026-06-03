import anthropic
import os

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    return _client

def get_coaching_message(trigger: str, context: dict) -> str:
    """
    Generate a personalized coaching message from Claude given a trigger and session context.

    Args:
        trigger: One of POSTURE_NUDGE, EARLY_BREAK, FLOW_EXTENSION, SESSION_END
        context: Dict with keys like focus_score, elapsed_mins, noise_level, top_app, blink_rate
    """
    focus = context.get("focus_score", 50)
    elapsed = context.get("elapsed_mins", 0)
    noise = context.get("noise_level_db", 40)
    app = context.get("top_app", "Unknown")
    blink_rate = context.get("blink_rate_per_min", 15)

    trigger_descriptions = {
        "POSTURE_NUDGE": "the user has been slouching for more than 70% of the last 30 seconds",
        "EARLY_BREAK": f"the user's focus dropped to {focus:.0f}% with {elapsed:.0f} minutes elapsed — triggering an early break",
        "FLOW_EXTENSION": f"the user is in a deep flow state with {focus:.0f}% focus — extending the work session",
        "SESSION_END": f"the user just completed a full study session of {elapsed:.0f} minutes",
    }

    description = trigger_descriptions.get(trigger, f"a {trigger} event occurred")

    prompt = f"""You are a warm, encouraging study coach embedded in a focus tracking app.
The following event just occurred: {description}.

Additional context:
- Current focus density score: {focus:.0f}%
- Ambient noise level: {noise:.0f} dB
- Most-used app in this session: {app}
- Blink rate: {blink_rate:.0f} blinks/min (normal is ~15–20; very high may indicate fatigue)

Write a single, brief (2–3 sentence) message to the user. Be warm, specific, and actionable.
Do NOT use markdown. Do NOT use bullet points. Speak directly to the user."""

    try:
        client = _get_client()
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        # Fallback messages if API unavailable
        fallbacks = {
            "POSTURE_NUDGE": "Hey, you've been slouching — sit up straight and take a breath!",
            "EARLY_BREAK": "Your focus has dipped. Take a short break — you've earned it.",
            "FLOW_EXTENSION": "You're in the zone! Extending your session by 5 minutes.",
            "SESSION_END": "Great session! Review what you accomplished before jumping into the next one.",
        }
        return fallbacks.get(trigger, "Keep going — you're doing great!")
