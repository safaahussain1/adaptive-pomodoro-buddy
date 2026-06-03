"""
Personal productivity dashboard.

Usage:
    python dashboard.py                 # show summary of all sessions
    python dashboard.py --advice        # also get LLM-generated personal advice
"""

import json
import os
import argparse
from datetime import datetime
from collections import defaultdict, Counter
from analytics import load_all_sessions, compute_session_summary

try:
    from llm_coach import _get_client
    import anthropic
    _LLM_AVAILABLE = True
except Exception:
    _LLM_AVAILABLE = False


def load_all_session_files(directory="."):
    """Return list of (filename, summary, logs) for every saved session."""
    sessions = []
    fnames = sorted(
        f for f in os.listdir(directory)
        if f.startswith("session_") and f.endswith(".json")
    )
    for fname in fnames:
        with open(os.path.join(directory, fname)) as f:
            data = json.load(f)
        # New format: {"summary": {...}, "logs": [...]}
        if isinstance(data, dict) and "logs" in data:
            logs = data["logs"]
            summary = data.get("summary") or compute_session_summary(logs)
        else:
            logs = data  # legacy flat list
            summary = compute_session_summary(logs)
        sessions.append((fname, summary, logs))
    return sessions


def hour_of_day_analysis(sessions):
    """Return dict mapping hour (0-23) -> avg focus %."""
    hour_focus = defaultdict(list)
    for _, _, logs in sessions:
        if not logs:
            continue
        start_hour = datetime.fromtimestamp(logs[0]["timestamp"]).hour
        focused = sum(1 for p in logs if p.get("gaze_score") == 1 and p.get("window_is_productive") == 1)
        total = len(logs)
        if total:
            hour_focus[start_hour].append(focused / total * 100)
    return {h: round(sum(vs) / len(vs), 1) for h, vs in sorted(hour_focus.items())}


def app_usage_analysis(sessions):
    """Return Counter of app → total seconds across all sessions."""
    app_counter = Counter()
    for _, _, logs in sessions:
        for p in logs:
            app_counter[p.get("active_app", "Unknown")] += 1
    return app_counter


def trend_over_sessions(sessions):
    """Return list of (date_str, focus_pct) for trend line."""
    trend = []
    for fname, summary, logs in sessions:
        if not logs or not summary:
            continue
        ts = logs[0]["timestamp"]
        date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
        trend.append((date_str, summary.get("overall_focus_pct", 0)))
    return trend


def bar(value, max_value=100, width=30, fill="█", empty="░"):
    filled = int(value / max_value * width)
    return fill * filled + empty * (width - filled)


def print_dashboard(sessions):
    if not sessions:
        print("No session data found. Run tracker.py first.")
        return

    print("\n" + "=" * 65)
    print("        ADAPTIVE POMODORO BUDDY — PERSONAL DASHBOARD")
    print("=" * 65)
    print(f"  Sessions recorded: {len(sessions)}")
    total_mins = sum(s.get("duration_mins", 0) for _, s, _ in sessions)
    print(f"  Total study time:  {total_mins:.0f} min ({total_mins/60:.1f} hours)")
    print()

    # ── Per-session table ────────────────────────────────────────────
    print("  SESSION HISTORY")
    print(f"  {'Date/Time':<18} {'Duration':>8} {'Focus':>7} {'Posture':>8} {'Top App':<25}")
    print("  " + "-" * 68)
    for fname, s, logs in sessions[-10:]:  # last 10
        if not logs:
            continue
        date = datetime.fromtimestamp(logs[0]["timestamp"]).strftime("%m/%d %H:%M")
        dur = f"{s.get('duration_mins', 0):.0f}m"
        foc = f"{s.get('overall_focus_pct', 0):.0f}%"
        pos = f"{s.get('good_posture_pct', 0):.0f}%"
        app = s.get("top_app", "?")[:24]
        print(f"  {date:<18} {dur:>8} {foc:>7} {pos:>8} {app:<25}")
    print()

    # ── Focus trend ──────────────────────────────────────────────────
    print("  FOCUS TREND (most recent sessions)")
    trend = trend_over_sessions(sessions)
    for date_str, focus in trend[-8:]:
        print(f"  {date_str:<18}  {bar(focus, width=25)} {focus:.0f}%")
    print()

    # ── Best hours ───────────────────────────────────────────────────
    hour_focus = hour_of_day_analysis(sessions)
    if hour_focus:
        print("  PRODUCTIVITY BY HOUR OF DAY")
        best_hour = max(hour_focus, key=hour_focus.get)
        for h, focus in sorted(hour_focus.items()):
            label = f"{h:02d}:00"
            marker = " ← best" if h == best_hour else ""
            print(f"  {label}  {bar(focus, width=20)} {focus:.0f}%{marker}")
        print()

    # ── App breakdown ────────────────────────────────────────────────
    app_counts = app_usage_analysis(sessions)
    total_samples = sum(app_counts.values()) or 1
    print("  APP USAGE ACROSS ALL SESSIONS")
    for app, count in app_counts.most_common(8):
        pct = count / total_samples * 100
        print(f"  {app:<30} {bar(pct, width=20)} {pct:.1f}%")
    print()

    # ── Averages ─────────────────────────────────────────────────────
    valid = [s for _, s, _ in sessions if s]
    if valid:
        avg_focus = sum(s.get("overall_focus_pct", 0) for s in valid) / len(valid)
        avg_posture = sum(s.get("good_posture_pct", 0) for s in valid) / len(valid)
        avg_noise = sum(s.get("avg_noise_db", 40) for s in valid) / len(valid)
        avg_blink = sum(s.get("avg_blink_rate_per_min", 15) for s in valid) / len(valid)
        print("  PERSONAL AVERAGES")
        print(f"  Focus density        : {avg_focus:.1f}%")
        print(f"  Good posture rate    : {avg_posture:.1f}%")
        print(f"  Avg ambient noise    : {avg_noise:.1f} dB")
        print(f"  Avg blink rate       : {avg_blink:.1f} blinks/min")
        print()

        # Strengths / weaknesses
        print("  STRENGTHS & AREAS TO IMPROVE")
        metrics = {
            "Focus density": avg_focus,
            "Good posture": avg_posture,
        }
        best = max(metrics, key=metrics.get)
        worst = min(metrics, key=metrics.get)
        print(f"  Strength : {best} ({metrics[best]:.0f}%)")
        print(f"  Improve  : {worst} ({metrics[worst]:.0f}%)")
        if avg_blink < 10:
            print("  Warning  : Very low blink rate — may indicate eye strain. Take more eye breaks.")
        elif avg_blink > 30:
            print("  Warning  : High blink rate — possible fatigue or eye irritation.")
        if avg_noise > 60:
            print("  Warning  : Average study environment is loud — consider noise-cancelling headphones.")
        print()

    print("=" * 65)


def get_llm_advice(sessions):
    if not _LLM_AVAILABLE:
        print("ANTHROPIC_API_KEY not set — skipping AI advice.")
        return

    valid = [s for _, s, _ in sessions if s]
    if not valid:
        return

    avg_focus = sum(s.get("overall_focus_pct", 0) for s in valid) / len(valid)
    avg_posture = sum(s.get("good_posture_pct", 0) for s in valid) / len(valid)
    avg_noise = sum(s.get("avg_noise_db", 40) for s in valid) / len(valid)
    hour_focus = hour_of_day_analysis(sessions)
    best_hour = max(hour_focus, key=hour_focus.get) if hour_focus else None
    app_counts = app_usage_analysis(sessions)
    top_apps = ", ".join(a for a, _ in app_counts.most_common(3))
    trend = trend_over_sessions(sessions)
    trend_str = " → ".join(f"{f:.0f}%" for _, f in trend[-5:]) if trend else "N/A"

    prompt = f"""You are a personal productivity coach. A student has been using an adaptive Pomodoro study tool.
Here is their aggregated data across {len(sessions)} study session(s):

- Average focus density: {avg_focus:.1f}%
- Average good posture rate: {avg_posture:.1f}%
- Average ambient noise: {avg_noise:.1f} dB
- Most productive hour of day: {best_hour}:00 (if data exists)
- Most-used apps: {top_apps}
- Focus trend (oldest to newest): {trend_str}

Write a personal, specific 4–6 sentence coaching note for this student. Cover:
1. Their biggest strength
2. Their most important area to improve and a concrete tip
3. The best time of day for them to study (based on hour data)
4. One specific environmental or behavioral change to try next session

Be direct, warm, and specific. No bullet points. No markdown."""

    try:
        client = _get_client()
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        print("\n  PERSONAL AI ADVICE")
        print("  " + "-" * 62)
        for line in resp.content[0].text.strip().split("\n"):
            print(f"  {line}")
        print()
    except Exception as e:
        print(f"  Could not fetch AI advice: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Adaptive Pomodoro personal dashboard")
    parser.add_argument("--advice", action="store_true", help="Include Claude-generated personal advice")
    args = parser.parse_args()

    sessions = load_all_session_files()
    print_dashboard(sessions)
    if args.advice:
        get_llm_advice(sessions)
