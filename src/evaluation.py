from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from src.copilot import CopilotRequest, generate_recommendations
from src.recommender import load_songs


def _scenario_cases() -> List[Dict]:
    return [
        {
            "name": "happy_pop",
            "request": CopilotRequest(intent="upbeat happy pop", genre="pop", mood="happy", energy=0.85, likes_acoustic=False, top_k=5),
            "expect_genre_one_of": {"pop", "indie pop", "edm"},
            "min_confidence": 0.55,
        },
        {
            "name": "study_focus",
            "request": CopilotRequest(intent="focus coding session", genre="lofi", mood="focused", energy=0.4, likes_acoustic=True, top_k=5),
            "expect_genre_one_of": {"lofi", "ambient"},
            "min_confidence": 0.45,
        },
        {
            "name": "intense_rock",
            "request": CopilotRequest(intent="intense workout set", genre="rock", mood="intense", energy=0.92, likes_acoustic=False, top_k=5),
            "expect_genre_one_of": {"rock", "metal", "edm"},
            "min_confidence": 0.55,
        },
    ]


def run_reliability_evaluation(log_path: str = "artifacts/reliability_report.json") -> Dict:
    songs = load_songs("data/songs.csv")
    scenarios = _scenario_cases()
    results = []
    passed = 0
    for case in scenarios:
        output = generate_recommendations(case["request"], songs)
        top_song = output["recommendations"][0]["song"] if output["recommendations"] else None
        genre_ok = bool(top_song and top_song["genre"] in case["expect_genre_one_of"])
        confidence_ok = output["confidence"] >= case["min_confidence"]
        ok = output["ok"] and genre_ok and confidence_ok
        passed += int(ok)
        results.append(
            {
                "name": case["name"],
                "ok": ok,
                "confidence": output["confidence"],
                "candidate_count": output.get("candidate_count", 0),
                "top_song": top_song["title"] if top_song else None,
                "top_genre": top_song["genre"] if top_song else None,
                "story_present": bool(output.get("story")),
                "error": output.get("error", ""),
            }
        )

    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "passed": passed,
        "total": len(scenarios),
        "pass_rate": round(passed / len(scenarios), 2),
        "results": results,
    }
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    report = run_reliability_evaluation()
    print(f"Reliability: {report['passed']}/{report['total']} passed (rate={report['pass_rate']:.2f})")
