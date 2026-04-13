"""
CLI: I load CSV -> loop profiles -> recommend_songs -> print top k with reasons.
"""

from pathlib import Path

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


if __name__ == "__main__":
    main()
