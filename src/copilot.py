"""
AI DJ Copilot orchestration:
- Parse user intent -> normalized preferences
- Retrieve candidate songs with light semantic expansion
- Rank + explain + confidence
- Generate playlist story
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.recommender import _genre_matches, score_song_detailed


_GENRE_ALIASES = {
    "workout": "edm",
    "gym": "edm",
    "lift": "rock",
    "focus": "lofi",
    "study": "lofi",
    "coding": "lofi",
    "drive": "synthwave",
    "chill": "ambient",
    "calm": "ambient",
    "party": "pop",
    "sleep": "classical",
}

_MOOD_ALIASES = {
    "happy": "happy",
    "upbeat": "happy",
    "chill": "chill",
    "calm": "relaxed",
    "focus": "focused",
    "intense": "intense",
    "moody": "moody",
    "sad": "sad",
}

_PERSONA_PRESETS = {
    "Gym Boost": {"genre": "edm", "mood": "intense", "energy": 0.9, "likes_acoustic": False},
    "Study Flow": {"genre": "lofi", "mood": "focused", "energy": 0.4, "likes_acoustic": True},
    "Night Drive": {"genre": "synthwave", "mood": "moody", "energy": 0.72, "likes_acoustic": False},
}


@dataclass
class CopilotRequest:
    intent: str
    genre: str
    mood: str
    energy: float
    likes_acoustic: Optional[bool]
    top_k: int = 5


def get_persona_presets() -> Dict[str, Dict]:
    return _PERSONA_PRESETS


def parse_intent(intent: str, base_prefs: Optional[Dict] = None) -> Dict:
    prefs = dict(base_prefs or {})
    text = intent.lower().strip()
    if text:
        for token, genre in _GENRE_ALIASES.items():
            if token in text and not prefs.get("genre"):
                prefs["genre"] = genre
                break
        for token, mood in _MOOD_ALIASES.items():
            if token in text and not prefs.get("mood"):
                prefs["mood"] = mood
                break
        if any(word in text for word in ("high energy", "pump", "hype", "intense")):
            prefs["energy"] = max(float(prefs.get("energy", 0.8)), 0.8)
        if any(word in text for word in ("chill", "calm", "wind down", "focus")):
            prefs["energy"] = min(float(prefs.get("energy", 0.45)), 0.45)
        if "acoustic" in text and "no acoustic" not in text:
            prefs["likes_acoustic"] = True
    return prefs


def validate_preferences(prefs: Dict) -> Tuple[bool, str, Dict]:
    normalized = dict(prefs)
    if not normalized.get("genre"):
        return False, "Please choose a genre or include one in your intent.", normalized
    if not normalized.get("mood"):
        return False, "Please choose a mood or include one in your intent.", normalized
    if "energy" not in normalized:
        normalized["energy"] = 0.6
    try:
        normalized["energy"] = min(1.0, max(0.0, float(normalized["energy"])))
    except (TypeError, ValueError):
        return False, "Energy must be a number between 0 and 1.", normalized
    if "likes_acoustic" not in normalized:
        normalized["likes_acoustic"] = None
    return True, "", normalized


def safe_defaults() -> Dict:
    return {"genre": "pop", "mood": "happy", "energy": 0.65, "likes_acoustic": False}


def _retrieval_bonus(song: Dict, prefs: Dict) -> float:
    bonus = 0.0
    genre = str(prefs.get("genre", "")).strip().lower()
    mood = str(prefs.get("mood", "")).strip().lower()
    song_genre = str(song["genre"]).strip().lower()
    song_mood = str(song["mood"]).strip().lower()

    if genre and _genre_matches(genre, song_genre):
        bonus += 0.35
    elif genre and genre in _GENRE_ALIASES and _GENRE_ALIASES.get(genre) == song_genre:
        bonus += 0.2

    if mood and mood == song_mood:
        bonus += 0.25
    elif mood and mood in _MOOD_ALIASES and _MOOD_ALIASES[mood] == song_mood:
        bonus += 0.15
    return bonus


def retrieve_candidates(songs: List[Dict], prefs: Dict) -> List[Dict]:
    with_bonus = []
    for song in songs:
        bonus = _retrieval_bonus(song, prefs)
        if bonus > 0 or not prefs.get("genre"):
            with_bonus.append((bonus, song))
    if not with_bonus:
        return songs
    with_bonus.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in with_bonus]


def _confidence_from_ranked(ranked: List[Dict], prefs: Dict) -> float:
    if not ranked:
        return 0.0
    top = ranked[0]["score"]
    second = ranked[1]["score"] if len(ranked) > 1 else 0.0
    margin = max(0.0, min(1.0, (top - second) / 2.0))
    coverage = 0.0
    if ranked[0]["contributions"]["genre"] > 0:
        coverage += 0.35
    if ranked[0]["contributions"]["mood"] > 0:
        coverage += 0.25
    coverage += min(0.4, ranked[0]["contributions"]["energy"] / 3.0 * 0.4)
    return round(min(1.0, margin * 0.4 + coverage * 0.6), 2)


def build_playlist_story(items: List[Dict], prefs: Dict, confidence: float) -> str:
    if not items:
        return "I could not build a strong playlist story because no good matches were found."
    lines = []
    lines.append(
        f"This set starts with a {prefs['mood']} tone in the {prefs['genre']} lane and targets energy around {prefs['energy']:.2f}."
    )
    energies = [float(item["song"]["energy"]) for item in items]
    if energies[-1] > energies[0]:
        arc = "builds momentum as the playlist progresses"
    elif energies[-1] < energies[0]:
        arc = "eases down from the opener into a smoother landing"
    else:
        arc = "keeps a stable energy profile throughout"
    lines.append(f"It {arc}.")
    top_titles = ", ".join(item["song"]["title"] for item in items[:3])
    lines.append(f"Anchor tracks include {top_titles}, chosen for strong mood/energy fit and retrieval relevance.")
    if confidence < 0.55:
        lines.append("Confidence is limited because candidate matches were sparse; use Refine to widen mood or genre.")
    return " ".join(lines)


def generate_recommendations(request: CopilotRequest, songs: List[Dict]) -> Dict:
    parsed = parse_intent(
        request.intent,
        {
            "genre": request.genre,
            "mood": request.mood,
            "energy": request.energy,
            "likes_acoustic": request.likes_acoustic,
        },
    )
    ok, error, prefs = validate_preferences(parsed)
    if not ok:
        result = {"ok": False, "error": error, "prefs": prefs, "recommendations": [], "confidence": 0.0, "story": ""}
        log_recommendation_event(result, request, 0)
        return result

    candidates = retrieve_candidates(songs, prefs)
    ranked = []
    for song in candidates:
        scoring_prefs = dict(prefs)
        scoring_prefs["_retrieval_boost"] = _retrieval_bonus(song, prefs)
        detail = score_song_detailed(scoring_prefs, song)
        ranked.append(
            {
                "song": song,
                "score": detail["score"],
                "reasons": detail["reasons"],
                "contributions": detail["contributions"],
            }
        )
    ranked.sort(key=lambda item: item["score"], reverse=True)
    top_items = ranked[: max(1, request.top_k)]
    confidence = _confidence_from_ranked(top_items, prefs)
    story = build_playlist_story(top_items, prefs, confidence)
    result = {
        "ok": True,
        "error": "",
        "prefs": prefs,
        "recommendations": top_items,
        "confidence": confidence,
        "story": story,
        "candidate_count": len(candidates),
        "guardrail_flags": ["low_confidence"] if confidence < 0.55 else [],
        "fallback_available": confidence < 0.55,
    }
    log_recommendation_event(result, request, len(candidates))
    return result


def log_recommendation_event(result: Dict, request: CopilotRequest, candidate_count: int, log_path: str = "artifacts/recommendation_log.jsonl") -> None:
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "intent": request.intent,
        "input": {
            "genre": request.genre,
            "mood": request.mood,
            "energy": request.energy,
            "likes_acoustic": request.likes_acoustic,
            "top_k": request.top_k,
        },
        "ok": result.get("ok", False),
        "error": result.get("error", ""),
        "confidence": result.get("confidence", 0.0),
        "guardrail_flags": result.get("guardrail_flags", []),
        "candidate_count": candidate_count,
        "top_titles": [item["song"]["title"] for item in result.get("recommendations", [])[:3]],
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")
