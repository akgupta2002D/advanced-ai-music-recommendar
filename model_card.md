# Model Card: AI DJ Copilot

## 1) Model Name

**AI DJ Copilot v2 (RAG-lite Hybrid Ranker)**

## 2) Intended Use

- **Primary task:** Generate personalized music recommendations and a narrative playlist story.
- **Audience:** Coursework demo and educational prototyping.
- **Not intended for:** production personalization at scale, safety-critical decisions, or commercial ranking experiments.

## 3) System Description

The system combines:
- **Intent parsing** to map free-form user requests to structured preferences.
- **Retriever** that boosts candidate songs using genre/mood semantic aliases.
- **Transparent ranker** that scores genre, mood, energy closeness, acousticness, and retrieval bonus.
- **Story generator** that explains overall playlist flow and transition logic.
- **Guardrails** that flag low-confidence outputs and offer safe default recovery.

## 4) Data

- Source: local synthetic catalog in `data/songs.csv` (~15 tracks).
- Features: genre, mood, energy, tempo, valence, danceability, acousticness.
- Limitations:
  - small and hand-curated dataset,
  - uneven genre representation,
  - no listener history or collaborative signal.

## 5) Strengths

- Recommendations are explainable through score contributions and reason strings.
- Reproducible, local, and fast to run (no external model dependency required).
- User flow supports refinement, not one-shot output.

## 6) Limitations and Biases

- Label bias: recommendations only reflect metadata quality and catalog coverage.
- Potential filter bubble: repeated genre preference can dominate ranking outcomes.
- Semantic gaps: alias-based retrieval is limited versus true embedding retrieval.
- Confidence score is heuristic and should be interpreted as directional only.

## 7) Reliability and Evaluation

- Unit tests cover ranking, parsing, validation, consistency, and story presence.
- Scenario-based reliability runner (`python -m src.evaluation`) reports pass rate and top result quality.
- Structured recommendation logs (`artifacts/recommendation_log.jsonl`) track confidence, guardrails, and top outputs.

## 8) Misuse Risks and Mitigations

- **Risk:** Users may treat recommendations as objective truth.  
  **Mitigation:** display reasons, confidence, and refinement controls.
- **Risk:** Overconfidence on sparse matches.  
  **Mitigation:** low-confidence flag + safer defaults path.
- **Risk:** Biased output due to catalog imbalance.  
  **Mitigation:** document limitations and encourage wider data coverage.

## 9) Reflection and Ethics

- **What surprised me in reliability testing:** Small weight changes can noticeably reorder top picks, especially in sparse genres.
- **Helpful AI collaboration example:** AI helped scaffold modular flow (parser -> retriever -> ranker -> story) faster than manual refactoring alone.
- **Flawed AI collaboration example:** An early AI suggestion overweighted retrieval boosts and reduced recommendation quality; I corrected this by capping retrieval impact so core scoring remains primary.

## 10) Future Improvements

- Add diversity constraints in top-k to reduce near-duplicate vibe picks.
- Upgrade retrieval from alias rules to embedding-based semantic similarity.
- Add human-in-the-loop thumbs up/down feedback to tune ranking weights.
