# streamlit_app.py
import json
import datetime as dt
from pathlib import Path

import streamlit as st
from app_core import generate_itinerary, get_popular_destinations


# ─────────────────────────────  PAGE CONFIG  ────────────────────────────────
st.set_page_config(page_title="Travel Itinerary Pitcher", page_icon="✈️")


# ─────────────────────────────  SESSION STATE  ──────────────────────────────
if "view_only" not in st.session_state:   # True when user opened a saved file
    st.session_state["view_only"] = False
if "last_prefs" not in st.session_state:
    st.session_state["last_prefs"] = None
if "last_result" not in st.session_state:
    st.session_state["last_result"] = None


# ─────────────────────────────  HELPERS  ────────────────────────────────────
SAVE_DIR = Path("saved_itineraries")
SAVE_DIR.mkdir(exist_ok=True)

def _save_itinerary(name: str, prefs: dict, data: dict) -> None:
    with (SAVE_DIR / f"{name}.json").open("w") as f:
        json.dump({"prefs": prefs, "data": data}, f, indent=2)

def _list_saved() -> list[str]:
    return sorted(p.stem for p in SAVE_DIR.glob("*.json"))

def _load_itinerary(name: str) -> dict:
    with (SAVE_DIR / f"{name}.json").open() as f:
        return json.load(f)

def _render_itinerary(prefs: dict, result: dict) -> None:
    """Pretty-print an itinerary in the main panel."""
    st.header(f"🗺️  {prefs['destination'].title()} — {prefs['trip_duration']} days")
    st.write(result["narrative"]["main_narrative"])

    with st.expander("In-depth itinerary"):
        for d in result["narrative"]["daily_plans"]:
            st.write(d["content"])

    with st.expander("Budget breakdown"):
        st.write(result["narrative"]["budget_narrative"])

    # ─── Quality score + breakdown ─────────────────────────────────────────
    if "scores" in result:
        total = result["scores"]["total"]
        st.markdown(f"### ⭐ Planner score: **{total}/100**")
        st.progress(int(total))

        with st.expander("Why this score?"):
            for metric, val in result["scores"].items():
                if metric == "total":
                    continue
                pct = f"{val*100:.1f}"
                st.write(f"- **{metric.replace('_', ' ').title()}**: {pct}")


# ─────────────────────────────  SIDEBAR  ────────────────────────────────────
st.sidebar.header("📁 Saved itineraries")
saved_names = _list_saved()

sel_name = st.sidebar.selectbox("Open", saved_names) if saved_names else None
if sel_name and st.sidebar.button("Open"):
    loaded = _load_itinerary(sel_name)
    st.session_state["last_prefs"]  = loaded["prefs"]
    st.session_state["last_result"] = loaded["data"]
    st.session_state["view_only"]   = True
    st.toast(f"Loaded “{sel_name}”")
    st.rerun()                       # restart script so main panel updates

st.sidebar.markdown("---")
st.sidebar.caption("Files live in local ‘saved_itineraries/’")


# ─────────────────────  VIEW-ONLY MODE (opened file)  ──────────────────────
if st.session_state["view_only"] and st.session_state["last_result"]:
    _render_itinerary(st.session_state["last_prefs"],
                      st.session_state["last_result"])

    if st.button("🔄  Back to generator"):
        st.session_state["view_only"] = False
        st.rerun()

    st.stop()           # nothing below runs while viewing a saved file


# ─────────────────────────────  MAIN UI FORM  ───────────────────────────────
dest_choices = sorted(d["name"] for d in get_popular_destinations())
dest_choices.append("Other…")

st.title("Travel-Itinerary-Pitcher ✈️")

prefs: dict = {}

# ── Destination (with free-text fallback) ───────────────────────────────────
chosen = st.selectbox(
    "Destination",
    dest_choices,
    index=0 if dest_choices else None,
    placeholder="Choose a destination…" if not dest_choices else None,
)

if chosen == "Other…":
    custom_dest = st.text_input("Type your destination")
    prefs["destination"] = custom_dest.strip()
else:
    prefs["destination"] = chosen

# ── Interests, budget, days ────────────────────────────────────────────────
prefs["interests"] = st.multiselect(
    "Interests",
    ["culture", "food", "nature", "nightlife", "history", "adventure"],
)
prefs["budget_level"] = st.selectbox(
    "Budget level", ["budget", "moderate", "luxury"]
)
prefs["trip_duration"] = st.slider("Duration (days)", 1, 14, 5)


# ─────────────────────────────  GENERATE  ───────────────────────────────────
if st.button("Generate"):
    if not prefs["destination"]:
        st.warning("Please choose a destination first.")
        st.stop()

    with st.spinner("Cooking up your itinerary…"):
        result = generate_itinerary(prefs)

    st.session_state["last_prefs"]  = prefs
    st.session_state["last_result"] = result
    st.session_state["view_only"]   = False   # stay in edit mode
    st.rerun()                                 # refresh page with results


# ─────────────────────────────  SHOW RESULT  ────────────────────────────────
if st.session_state["last_result"]:
    _render_itinerary(st.session_state["last_prefs"],
                      st.session_state["last_result"])


# ─────────────────────────────  SAVE SECTION  ───────────────────────────────
if not st.session_state["view_only"] and st.session_state["last_result"]:
    st.markdown("---")
    st.subheader("Save this itinerary")

    default_name = (
        f"{st.session_state['last_prefs']['destination'].replace(' ', '_')}_"
        f"{dt.date.today().isoformat()}"
    )
    fname = st.text_input("File name", value=default_name)

    if st.button("Save"):
        if not fname.strip():
            st.warning("Please give the file a name.")
        else:
            _save_itinerary(fname.strip(),
                            st.session_state["last_prefs"],
                            st.session_state["last_result"])
            st.success(f"Saved as “{fname}.json”")
            st.rerun()                # refresh sidebar list
