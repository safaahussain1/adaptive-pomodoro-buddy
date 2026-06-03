import json
import os
from collections import Counter
from datetime import datetime


def load_all_sessions(history_dir: str = ".") -> list[dict]:
    logs = []
    for fname in os.listdir(history_dir):
        if fname.startswith("session_") and fname.endswith(".json"):
            with open(os.path.join(history_dir, fname)) as f:
                logs.extend(json.load(f))
    # Also load legacy session_history.json
    legacy = os.path.join(history_dir, "session_history.json")
    if os.path.exists(legacy):
        with open(legacy) as f:
            logs.extend(json.load(f))
    return logs


def compute_session_summary(logs: list[dict]) -> dict:
    if not logs:
        return {}

    total_frames = len(logs)
    focused_frames = sum(1 for p in logs if p.get("gaze_score") == 1 and p.get("window_is_productive") == 1)
    good_posture_frames = sum(1 for p in logs if p.get("posture_score") == 1)
    avg_noise_db = (
        sum(p.get("noise_db", 40) for p in logs) / total_frames
    )
    avg_blink_rate = sum(p.get("blinks_in_last_sec", 0) for p in logs) * 60 / total_frames

    app_counts = Counter(p.get("active_app", "Unknown") for p in logs)
    top_app = app_counts.most_common(1)[0][0] if app_counts else "Unknown"

    work_frames = [p for p in logs if p.get("is_working_block")]
    break_frames = [p for p in logs if not p.get("is_working_block")]
    work_focus = (
        sum(1 for p in work_frames if p.get("gaze_score") == 1 and p.get("window_is_productive") == 1)
        / len(work_frames) * 100
        if work_frames else 0
    )

    start_ts = logs[0]["timestamp"]
    end_ts = logs[-1]["timestamp"]
    duration_mins = (end_ts - start_ts) / 60

    return {
        "duration_mins": round(duration_mins, 1),
        "total_samples": total_frames,
        "overall_focus_pct": round(focused_frames / total_frames * 100, 1),
        "work_focus_pct": round(work_focus, 1),
        "good_posture_pct": round(good_posture_frames / total_frames * 100, 1),
        "avg_noise_db": round(avg_noise_db, 1),
        "avg_blink_rate_per_min": round(avg_blink_rate, 1),
        "top_app": top_app,
        "app_breakdown": dict(app_counts.most_common(5)),
    }


def print_session_report(logs: list[dict]):
    summary = compute_session_summary(logs)
    if not summary:
        print("No session data found.")
        return

    print("\n" + "=" * 55)
    print("       ADAPTIVE POMODORO BUDDY — SESSION REPORT")
    print("=" * 55)
    print(f"  Session duration       : {summary['duration_mins']} min")
    print(f"  Overall focus density  : {summary['overall_focus_pct']}%")
    print(f"  Focus during work      : {summary['work_focus_pct']}%")
    print(f"  Good posture rate      : {summary['good_posture_pct']}%")
    print(f"  Avg ambient noise      : {summary['avg_noise_db']} dB")
    print(f"  Avg blink rate         : {summary['avg_blink_rate_per_min']} blinks/min")
    print(f"  Top app used           : {summary['top_app']}")
    print("\n  App breakdown:")
    for app, count in summary["app_breakdown"].items():
        pct = round(count / summary["total_samples"] * 100, 1)
        print(f"    {app:<30} {pct:>5}%")
    print("=" * 55 + "\n")


def save_session_report(logs: list[dict], out_dir: str = "."):
    summary = compute_session_summary(logs)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(out_dir, f"session_{ts}.json")
    with open(path, "w") as f:
        json.dump({"summary": summary, "logs": logs}, f, indent=2)
    return path
