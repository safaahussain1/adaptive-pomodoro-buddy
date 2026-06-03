"""
Web dashboard for Adaptive Pomodoro Buddy.

Run:
    python web_dashboard.py
Then open http://localhost:5050 in any browser.
"""

import json
import os
from datetime import datetime
from collections import Counter, defaultdict
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

SESSION_DIR = os.path.dirname(os.path.abspath(__file__))

OWN_PROCESS_NAMES = {"Python", "python", "python3", "Adaptive Pomodoro Buddy", "Unknown"}


def load_sessions():
    sessions = []
    fnames = (
        f for f in os.listdir(SESSION_DIR)
        if f.startswith("session_") and f.endswith(".json")
    )
    for fname in fnames:
        path = os.path.join(SESSION_DIR, fname)
        with open(path) as f:
            raw = json.load(f)
        logs = raw["logs"] if isinstance(raw, dict) and "logs" in raw else raw
        if not logs:
            continue
        sessions.append({"fname": fname, "logs": logs})
    # Sort by actual session start time, not filename
    sessions.sort(key=lambda s: s["logs"][0]["timestamp"])
    return sessions


def compute_summary(logs):
    if not logs:
        return {}
    total = len(logs)
    focused = sum(1 for p in logs if p.get("gaze_score") == 1 and p.get("window_is_productive") == 1)
    good_posture = sum(1 for p in logs if p.get("posture_score") == 1)
    app_counts = Counter(
        p.get("active_app", "Unknown") for p in logs
        if p.get("active_app") not in OWN_PROCESS_NAMES
    )
    top_app = app_counts.most_common(1)[0][0] if app_counts else "Unknown"
    avg_noise = sum(p.get("noise_db", 40) for p in logs) / total
    avg_blink = sum(p.get("blinks_in_last_sec", 0) for p in logs) * 60 / total
    start_ts = logs[0]["timestamp"]
    end_ts = logs[-1]["timestamp"]
    duration_mins = (end_ts - start_ts) / 60
    work_logs = [p for p in logs if p.get("is_working_block")]
    work_focus = (
        sum(1 for p in work_logs if p.get("gaze_score") == 1 and p.get("window_is_productive") == 1)
        / len(work_logs) * 100 if work_logs else 0
    )
    return {
        "date": datetime.fromtimestamp(start_ts).strftime("%b %d, %Y"),
        "time": datetime.fromtimestamp(start_ts).strftime("%I:%M %p"),
        "hour": datetime.fromtimestamp(start_ts).hour,
        "duration_mins": round(duration_mins, 1),
        "overall_focus_pct": round(focused / total * 100, 1),
        "work_focus_pct": round(work_focus, 1),
        "good_posture_pct": round(good_posture / total * 100, 1),
        "avg_noise_db": round(avg_noise, 1),
        "avg_blink_rate": round(avg_blink, 1),
        "top_app": top_app,
        "app_breakdown": {
            k: round(v / total * 100, 1)
            for k, v in app_counts.most_common(6)
            if k not in OWN_PROCESS_NAMES
        },
        "total_samples": total,
    }


@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/api/data")
def api_data():
    sessions = load_sessions()
    summaries = []
    for s in sessions:
        summary = compute_summary(s["logs"])
        if summary:
            summaries.append(summary)

    if not summaries:
        return jsonify({"sessions": [], "aggregates": {}, "hourly": {}, "apps": {}})

    # Aggregates
    avg_focus = sum(s["overall_focus_pct"] for s in summaries) / len(summaries)
    avg_posture = sum(s["good_posture_pct"] for s in summaries) / len(summaries)
    avg_noise = sum(s["avg_noise_db"] for s in summaries) / len(summaries)
    total_mins = sum(s["duration_mins"] for s in summaries)

    # Hourly productivity
    hour_focus = defaultdict(list)
    for s in summaries:
        hour_focus[s["hour"]].append(s["overall_focus_pct"])
    hourly = {h: round(sum(vs) / len(vs), 1) for h, vs in sorted(hour_focus.items())}

    # App usage across all sessions
    all_logs = []
    for s in sessions:
        all_logs.extend(s["logs"])
    app_counter = Counter(
        p.get("active_app", "Unknown") for p in all_logs
        if p.get("active_app") not in OWN_PROCESS_NAMES
    )
    total_app_samples = sum(app_counter.values()) or 1
    apps = {
        k: round(v / total_app_samples * 100, 1)
        for k, v in app_counter.most_common(8)
    }

    # Trend (for chart)
    trend = [
        {"date": s["date"] + " " + s["time"], "focus": s["overall_focus_pct"]}
        for s in summaries
    ]

    # Best hour
    best_hour = max(hourly, key=hourly.get) if hourly else None

    # Strengths / weaknesses
    insights = []
    if avg_focus >= 70:
        insights.append({"type": "strength", "text": f"Strong focus — averaging {avg_focus:.0f}% across sessions."})
    elif avg_focus < 40:
        insights.append({"type": "warning", "text": f"Focus density is low ({avg_focus:.0f}%). Try closing distracting tabs before starting."})
    if avg_posture >= 70:
        insights.append({"type": "strength", "text": f"Great posture habits — {avg_posture:.0f}% of time with good alignment."})
    elif avg_posture < 50:
        insights.append({"type": "warning", "text": f"Posture needs attention ({avg_posture:.0f}%). Consider raising your monitor."})
    if best_hour is not None:
        insights.append({"type": "tip", "text": f"You're most productive at {best_hour}:00. Schedule your hardest tasks then."})
    if avg_noise > 60:
        insights.append({"type": "warning", "text": f"Avg noise is {avg_noise:.0f} dB — quite loud. Noise-cancelling headphones may help."})
    avg_blink = sum(s["avg_blink_rate"] for s in summaries) / len(summaries)
    if avg_blink < 10:
        insights.append({"type": "warning", "text": f"Blink rate is low ({avg_blink:.0f}/min). Look away from the screen for 20 seconds every 20 minutes."})

    return jsonify({
        "sessions": summaries,
        "trend": trend,
        "aggregates": {
            "avg_focus": round(avg_focus, 1),
            "avg_posture": round(avg_posture, 1),
            "avg_noise": round(avg_noise, 1),
            "total_mins": round(total_mins, 0),
            "session_count": len(summaries),
            "best_hour": best_hour,
        },
        "hourly": hourly,
        "apps": apps,
        "insights": insights,
    })


@app.route("/api/advice")
def api_advice():
    """Generate personalized advice via Gemini (called on demand)."""
    try:
        from llm_coach import _get_model
        sessions = load_sessions()
        summaries = [compute_summary(s["logs"]) for s in sessions]
        summaries = [s for s in summaries if s]
        if not summaries:
            return jsonify({"advice": "No session data yet. Run a few sessions first!"})

        avg_focus = sum(s["overall_focus_pct"] for s in summaries) / len(summaries)
        avg_posture = sum(s["good_posture_pct"] for s in summaries) / len(summaries)
        avg_noise = sum(s["avg_noise_db"] for s in summaries) / len(summaries)
        avg_blink = sum(s["avg_blink_rate"] for s in summaries) / len(summaries)
        all_logs = []
        for s in sessions:
            all_logs.extend(s["logs"])
        app_counter = Counter(
            p.get("active_app", "Unknown") for p in all_logs
            if p.get("active_app") not in OWN_PROCESS_NAMES
        )
        top_apps = ", ".join(a for a, _ in app_counter.most_common(3))
        hour_focus = defaultdict(list)
        for s in summaries:
            hour_focus[s["hour"]].append(s["overall_focus_pct"])
        best_hour = max(hour_focus, key=lambda h: sum(hour_focus[h]) / len(hour_focus[h])) if hour_focus else None
        trend_str = " → ".join(f"{s['overall_focus_pct']:.0f}%" for s in summaries[-5:])

        prompt = f"""You are a personal productivity coach. A student has been using an adaptive Pomodoro study tool.
Here is their aggregated data across {len(summaries)} study session(s):

- Average focus density: {avg_focus:.1f}%
- Average good posture rate: {avg_posture:.1f}%
- Average ambient noise: {avg_noise:.1f} dB
- Average blink rate: {avg_blink:.1f} blinks/min (normal is 15-20)
- Most productive hour: {best_hour}:00
- Most-used apps: {top_apps}
- Focus trend (oldest → newest): {trend_str}

Write a personal, specific 5–6 sentence coaching note. Cover:
1. Their biggest strength based on the data
2. Their most important area to improve with a concrete tip
3. Best time of day for deep work (based on hourly data)
4. One specific environmental or behavioral change for next session
5. An encouraging closing sentence

Be direct, warm, and specific. No bullet points. No markdown. Write as flowing paragraphs."""

        client = _get_model()
        from llm_coach import MODEL
        resp = client.models.generate_content(model=MODEL, contents=prompt)
        return jsonify({"advice": resp.text.strip()})
    except Exception as e:
        return jsonify({"advice": f"Could not generate advice: {e}"}), 500


if __name__ == "__main__":
    print("=" * 50)
    print("  Pomodoro Buddy Dashboard → http://localhost:5050")
    print("=" * 50)
    app.run(port=5050, debug=False)
