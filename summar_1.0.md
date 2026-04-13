# Project Summary (1.0)

## What this project is

This repository is a **starter codebase for CodePath AI 101 (Module 3): a Music Recommender Simulation**. It is a small, classroom-scale exercise in building a transparent recommender: you represent songs and user taste as structured data, define how to score and rank songs, print top picks with short explanations, and reflect on strengths, limits, and bias—similar in spirit to how real streaming recommenders turn signals into suggestions, but without production-scale data or machine learning infrastructure.

## What you implement

The core logic lives in `src/recommender.py`. You fill in **TODO** placeholders for:

- **`load_songs`**: Read `data/songs.csv` and return a list of song dictionaries for the CLI path.
- **`recommend_songs`**: Given simple preference keys (for example genre, mood, energy) and a catalog, score songs, rank them, and return the top `k` as tuples of `(song_dict, score, explanation)`.
- **`Recommender.recommend` / `explain_recommendation`**: Object-oriented API using `Song` and `UserProfile` dataclasses, aligned with `tests/test_recommender.py`.

The starter returns empty lists and placeholder explanations so tests and the CLI serve as a specification to grow into.

## Data and features

`songs.csv` is a **tiny synthetic catalog** of tracks with attributes such as genre, mood, energy, tempo (BPM), valence, danceability, and acousticness—enough to practice feature-based scoring and to see how weighting choices change outcomes.

## How it is meant to be used

- **Run the demo**: `python -m src.main` loads preferences, calls `recommend_songs`, and prints ranked results with explanations.
- **Verify behavior**: `pytest` runs tests that expect sensible ordering (for example, a pop / happy / high-energy profile should favor a matching song over a chill lofi track in the small fixture set).
- **Document the system**: `README.md` guides design write-ups and experiments; `model_card.md` prompts a structured description of intended use, data, limitations, evaluation, and reflection.

## Dependencies

`requirements.txt` lists **pandas**, **pytest**, and **streamlit** (Streamlit may be optional for your course variant; the checked-in runner is the CLI in `src/main.py`).

---

*This file summarizes the **starter** state of the project: the educational goal and layout, not a particular student’s finished recommender design.*
