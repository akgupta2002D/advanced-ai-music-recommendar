"""CLI demo for AI DJ Copilot and baseline recommender."""

from pathlib import Path

from src.copilot import CopilotRequest, generate_recommendations, get_persona_presets
from src.recommender import load_songs, recommend_songs

# project root so data path works when I run: python -m src.main
_ROOT = Path(__file__).resolve().parent.parent


def _print_block(title: str, user_prefs: dict, songs: list, k: int = 5) -> None:
    """I show one profile's rankings: prefs -> scores -> terminal lines."""
    print(f"\n--- {title} ---")
    recs = recommend_songs(user_prefs, songs, k=k)
    for song, score, explanation in recs:
        print(f"{song['title']} — {score:.2f}")
        print(f"  Because: {explanation}")
        print()


def main() -> None:
    # CSV on disk -> list[dict] I can score
    songs = load_songs(str(_ROOT / "data" / "songs.csv"))
    print(f"\nCatalog: {len(songs)} songs\n")

    # three tastes -> three ranked lists (stress-test my weights)
    _print_block(
        "Happy high-energy pop",
        {"genre": "pop", "mood": "happy", "energy": 0.85, "likes_acoustic": False},
        songs,
    )
    _print_block(
        "Chill lofi",
        {"genre": "lofi", "mood": "chill", "energy": 0.35, "likes_acoustic": True},
        songs,
    )
    _print_block(
        "Intense rock",
        {"genre": "rock", "mood": "intense", "energy": 0.9, "likes_acoustic": False},
        songs,
    )

    print("\n=== AI DJ Copilot demo ===")
    presets = get_persona_presets()
    for name, prefs in presets.items():
        req = CopilotRequest(
            intent=f"{name.lower()} with smooth transitions",
            genre=prefs["genre"],
            mood=prefs["mood"],
            energy=float(prefs["energy"]),
            likes_acoustic=prefs["likes_acoustic"],
            top_k=3,
        )
        result = generate_recommendations(req, songs)
        print(f"\n{name} | confidence={result['confidence']:.2f} | candidates={result.get('candidate_count', 0)}")
        if not result["ok"]:
            print(f"  Error: {result['error']}")
            continue
        print(f"  Story: {result['story']}")
        for item in result["recommendations"]:
            print(f"  - {item['song']['title']} ({item['score']:.2f})")


if __name__ == "__main__":
    main()
