from src.recommender import Song, UserProfile, Recommender
from src.copilot import CopilotRequest, generate_recommendations, parse_intent, validate_preferences
from src.recommender import load_songs

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


def test_intent_parser_infers_focus_lofi_defaults():
    parsed = parse_intent("focus coding session", {})
    assert parsed["genre"] == "lofi"
    assert parsed["mood"] == "focused"


def test_validate_preferences_rejects_missing_required_fields():
    ok, error, _ = validate_preferences({"energy": 0.7})
    assert ok is False
    assert "genre" in error.lower()


def test_copilot_recommendations_are_consistent_across_runs():
    songs = load_songs("data/songs.csv")
    req = CopilotRequest(
        intent="upbeat happy pop",
        genre="pop",
        mood="happy",
        energy=0.85,
        likes_acoustic=False,
        top_k=3,
    )
    first = generate_recommendations(req, songs)
    second = generate_recommendations(req, songs)
    assert first["ok"] is True
    assert second["ok"] is True
    assert first["recommendations"][0]["song"]["title"] == second["recommendations"][0]["song"]["title"]


def test_playlist_story_is_generated_with_confidence():
    songs = load_songs("data/songs.csv")
    req = CopilotRequest(
        intent="night drive and moody",
        genre="synthwave",
        mood="moody",
        energy=0.72,
        likes_acoustic=False,
        top_k=5,
    )
    result = generate_recommendations(req, songs)
    assert result["ok"] is True
    assert result["story"].strip() != ""
    assert 0.0 <= result["confidence"] <= 1.0
