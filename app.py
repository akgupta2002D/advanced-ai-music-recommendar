from __future__ import annotations

import streamlit as st

from src.copilot import CopilotRequest, generate_recommendations, get_persona_presets, safe_defaults
from src.recommender import load_songs


st.set_page_config(page_title="AI DJ Copilot", page_icon="🎧", layout="wide")


@st.cache_data
def get_songs():
    return load_songs("data/songs.csv")


def _init_state():
    defaults = {
        "step": 1,
        "intent": "",
        "genre": "",
        "mood": "",
        "energy": 0.65,
        "likes_acoustic": False,
        "result": None,
        "last_error": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _apply_persona(name: str):
    presets = get_persona_presets()
    if name in presets:
        profile = presets[name]
        st.session_state["genre"] = profile["genre"]
        st.session_state["mood"] = profile["mood"]
        st.session_state["energy"] = float(profile["energy"])
        st.session_state["likes_acoustic"] = bool(profile["likes_acoustic"])
        st.session_state["intent"] = f"{name.lower()} vibe"


def _progress_label(step: int) -> str:
    labels = {
        1: "1/4 Goal",
        2: "2/4 Preferences",
        3: "3/4 Generate",
        4: "4/4 Refine",
    }
    return labels.get(step, "1/4 Goal")


_init_state()
songs = get_songs()

st.title("AI DJ Copilot")
st.caption("Build a vibe-driven playlist with transparent AI reasoning and reliability checks.")
st.progress(st.session_state["step"] / 4.0, text=_progress_label(st.session_state["step"]))

with st.container(border=True):
    st.subheader("Quick start")
    persona_cols = st.columns(3)
    for idx, name in enumerate(get_persona_presets().keys()):
        if persona_cols[idx].button(name, use_container_width=True):
            _apply_persona(name)
            st.session_state["step"] = 2


if st.session_state["step"] == 1:
    with st.container(border=True):
        st.subheader("Step 1 - What should this playlist feel like?")
        st.session_state["intent"] = st.text_input(
            "Describe the vibe",
            value=st.session_state["intent"],
            placeholder="Example: gym opener then cool down, upbeat but not too loud",
        )
        if st.button("Continue to preference tuning", type="primary"):
            st.session_state["step"] = 2
            st.rerun()

elif st.session_state["step"] == 2:
    with st.container(border=True):
        st.subheader("Step 2 - Tune your preferences")
        left, right = st.columns(2)
        with left:
            st.session_state["genre"] = st.selectbox(
                "Genre", options=["", "pop", "lofi", "rock", "ambient", "edm", "synthwave", "jazz", "indie", "reggae", "classical", "metal"], index=0
            ) if not st.session_state["genre"] else st.text_input("Genre", value=st.session_state["genre"])
            st.session_state["mood"] = st.selectbox(
                "Mood", options=["", "happy", "chill", "focused", "intense", "moody", "relaxed", "sad"], index=0
            ) if not st.session_state["mood"] else st.text_input("Mood", value=st.session_state["mood"])
        with right:
            st.session_state["energy"] = st.slider("Target energy", 0.0, 1.0, float(st.session_state["energy"]), 0.01)
            st.session_state["likes_acoustic"] = st.toggle("Prefer acoustic tracks", value=bool(st.session_state["likes_acoustic"]))
        nav_left, nav_right = st.columns(2)
        if nav_left.button("Back"):
            st.session_state["step"] = 1
            st.rerun()
        if nav_right.button("Generate recommendations", type="primary"):
            st.session_state["step"] = 3
            st.rerun()

elif st.session_state["step"] == 3:
    with st.container(border=True):
        st.subheader("Step 3 - Your recommendations")
        request = CopilotRequest(
            intent=st.session_state["intent"],
            genre=st.session_state["genre"],
            mood=st.session_state["mood"],
            energy=float(st.session_state["energy"]),
            likes_acoustic=st.session_state["likes_acoustic"],
            top_k=5,
        )
        result = generate_recommendations(request, songs)
        st.session_state["result"] = result
        if not result["ok"]:
            st.error(result["error"])
            st.session_state["last_error"] = result["error"]
        else:
            st.success(f"Confidence: {result['confidence']:.2f} | Candidates considered: {result['candidate_count']}")
            st.markdown(f"**Playlist story:** {result['story']}")
            for idx, item in enumerate(result["recommendations"], start=1):
                song = item["song"]
                with st.container(border=True):
                    st.markdown(f"**#{idx} {song['title']} - {song['artist']}**")
                    st.caption(f"Genre: {song['genre']} | Mood: {song['mood']} | Energy: {song['energy']:.2f}")
                    st.write(f"Score: `{item['score']:.2f}`")
                    st.write("Why this song: " + "; ".join(item["reasons"]))
        nav_left, nav_right = st.columns(2)
        if nav_left.button("Back to preferences"):
            st.session_state["step"] = 2
            st.rerun()
        if nav_right.button("Refine results", type="primary"):
            st.session_state["step"] = 4
            st.rerun()

elif st.session_state["step"] == 4:
    with st.container(border=True):
        st.subheader("Step 4 - Refine")
        st.write("Adjust one or two controls and regenerate.")
        st.session_state["energy"] = st.slider("Energy override", 0.0, 1.0, float(st.session_state["energy"]), 0.01)
        loosen = st.toggle("Loosen to safer defaults")
        if loosen:
            defaults = safe_defaults()
            for key, value in defaults.items():
                st.session_state[key] = value
            st.info("Applied safer defaults to recover from low-confidence or invalid settings.")
        nav_left, nav_right = st.columns(2)
        if nav_left.button("Back to results"):
            st.session_state["step"] = 3
            st.rerun()
        if nav_right.button("Regenerate", type="primary"):
            st.session_state["step"] = 3
            st.rerun()
