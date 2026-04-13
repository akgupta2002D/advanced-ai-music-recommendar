# Model Card: Music Recommender Simulation

## 1. Model Name

**VibeRank CSV 1.0**

## 2. Intended Use

- **Task:** Suggest top tracks from a small local catalog using **genre, mood, energy**, plus a light **acoustic** nudge.
- **Who:** Me exploring how **prefs → score → sort** works.
- **Not for:** Real users, A/B tests, or safety-sensitive decisions.

## 3. How the Model Works

I give points when the user’s **genre** appears in the song’s genre label and when **mood** matches exactly. For **energy**, I reward songs **closer** to the user’s target (not “higher energy always wins”). If `likes_acoustic` is set, I tilt toward higher or lower **acousticness**. I sum points, sort descending, return the top few, and **string together the reasons** I added along the way.

## 4. Data

- **~15** synthetic songs in `data/songs.csv` (I added a few genres: edm, metal, reggae, classical, etc.).
- **Limits:** fake titles, uneven genre coverage, no release year or popularity.

## 5. Strengths

- **Explainable:** every score has human-readable “because” fragments.
- **Fast / simple:** no training loop; easy to audit in Python.
- **Profiles:** happy pop vs chill lofi vs intense rock **separate** in sensible ways on my runs.

## 6. Limitations and Bias

I only see **hand-picked tags**, so **synonyms** (rock vs metal) and **subcultures** collapse badly. Energy-only users can still get **mood mismatches** if genre lines up. A bigger risk is **self-reinforcement**: if the CSV skews pop, my **+2 genre** rule can **crowd out** mood-only fits—classic **filter bubble** risk if this were a real feed.

## 7. Evaluation

- **`pytest`** on the `Recommender` fixture (pop/happy/high energy should beat chill lofi).
- **Manual:** `python -m src.main` with three dict profiles; I read top 5 lists for sanity.
- **Surprise:** `Bass Bunker` can sneak high on “happy pop” via mood+energy even without genre—shows how **weight balance** changes who “wins.”

## 8. Future Work

- Add **diversity** in top-*k* (avoid near-duplicate vibes).
- **Genre families** (map metal→rock for certain users).
- Use **valence / danceability** with clear user knobs.

## 9. Personal Reflection

The biggest learning was separating **“score one row”** from **“rank the table”**—same math, two roles. I used AI for speed, but I **re-checked** weights against tests and my gut. Simple sums already feel “smart”; that makes me **more cautious** about opaque production recommenders.
