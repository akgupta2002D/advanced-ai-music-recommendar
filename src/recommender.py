"""
I turn CSV rows + user prefs -> scores -> ranked picks.
Flow: prefs + song -> score_song -> (points, reasons) -> recommend_songs sorts -> top k.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# --- weights (tune catalog behavior here) ---
_GENRE_MATCH = 2.0
_MOOD_MATCH = 1.0
_ENERGY_WEIGHT = 3.0  # I scale (1 - |song_energy - target|) so closer vibes score higher
_ACOUSTIC_WEIGHT = 0.5  # I nudge toward/away acoustic tracks when likes_acoustic is set


@dataclass
class Song:
    """One track in the catalog; tests expect this shape."""

    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float


@dataclass
class UserProfile:
    """Taste I compare against each Song (OOP path)."""

    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool


def _prefs_from_user(user: UserProfile) -> Dict:
    """I map UserProfile -> dict so one scoring path feeds CLI + tests."""
    return {
        "genre": user.favorite_genre,
        "mood": user.favorite_mood,
        "energy": user.target_energy,
        "likes_acoustic": user.likes_acoustic,
    }


def _genre_matches(pref: str, song_genre: str) -> bool:
    """I treat substring match as OK so 'pop' hits 'indie pop'."""
    p, g = pref.lower().strip(), song_genre.lower().strip()
    return p == g or p in g


def _energy_points(song_energy: float, target: float) -> Tuple[float, str]:
    """Closer energy -> higher points: target -> closeness -> weight * closeness."""
    closeness = max(0.0, 1.0 - abs(float(song_energy) - float(target)))
    pts = _ENERGY_WEIGHT * closeness
    return pts, f"energy closeness (+{pts:.2f})"


def _acoustic_points(song: Dict, likes: Optional[bool]) -> Tuple[float, List[str]]:
    """If likes_acoustic set, I reward high/low acousticness to match taste."""
    if likes is None:
        return 0.0, []
    ac = float(song["acousticness"])
    if likes:
        pts = _ACOUSTIC_WEIGHT * ac
    else:
        pts = _ACOUSTIC_WEIGHT * (1.0 - ac)
    return pts, [f"acoustic fit (+{pts:.2f})"]


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    I judge one song: prefs + row -> total score + reason strings.
    Flow: genre? -> mood? -> energy gap -> optional acoustic nudge.
    """
    score = 0.0
    reasons: List[str] = []

    g = user_prefs.get("genre", "")
    if g and _genre_matches(str(g), str(song["genre"])):
        score += _GENRE_MATCH
        reasons.append(f"genre match (+{_GENRE_MATCH})")

    m = user_prefs.get("mood", "")
    if m and str(m).lower().strip() == str(song["mood"]).lower().strip():
        score += _MOOD_MATCH
        reasons.append(f"mood match (+{_MOOD_MATCH})")

    if "energy" in user_prefs:
        epts, ers = _energy_points(float(song["energy"]), float(user_prefs["energy"]))
        score += epts
        reasons.append(ers)

    apts, areasons = _acoustic_points(song, user_prefs.get("likes_acoustic"))
    score += apts
    reasons.extend(areasons)

    return score, reasons


class Recommender:
    """I wrap Song objects and delegate scoring through score_song."""

    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Catalog -> score each as dict -> sort by score desc -> first k Song refs."""
        prefs = _prefs_from_user(user)
        scored: List[Tuple[float, Song]] = []
        for s in self.songs:
            d = asdict(s)
            total, _ = score_song(prefs, d)
            scored.append((total, s))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """I reuse score_song so explanations match the same math as ranking."""
        _, reasons = score_song(_prefs_from_user(user), asdict(song))
        return "; ".join(reasons) if reasons else "no strong matches; low fit"


def load_songs(csv_path: str) -> List[Dict]:
    """
    I read CSV -> list[dict] with numeric types cast for math.
    Flow: path -> open -> DictReader -> coerce int/float fields.
    """
    path = Path(csv_path)
    print(f"Loading songs from {path}...")
    rows: List[Dict] = []
    with path.open(newline="", encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            row = dict(raw)
            row["id"] = int(row["id"])
            row["title"] = str(row["title"])
            row["artist"] = str(row["artist"])
            row["genre"] = str(row["genre"])
            row["mood"] = str(row["mood"])
            for key in ("energy", "tempo_bpm", "valence", "danceability", "acousticness"):
                row[key] = float(row[key])
            row["tempo_bpm"] = int(round(row["tempo_bpm"]))
            rows.append(row)
    print(f"Loaded songs: {len(rows)}")
    return rows


def recommend_songs(
    user_prefs: Dict, songs: List[Dict], k: int = 5
) -> List[Tuple[Dict, float, str]]:
    """
    I rank the whole catalog for CLI: each song -> score_song -> sort -> top k tuples.
    """
    if not songs or k <= 0:
        return []
    ranked: List[Tuple[Dict, float, str]] = []
    for song in songs:
        total, reasons = score_song(user_prefs, song)
        expl = "; ".join(reasons) if reasons else "low match"
        ranked.append((song, total, expl))
    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked[:k]
