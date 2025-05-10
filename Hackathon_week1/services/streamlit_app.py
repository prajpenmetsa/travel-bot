# streamlit_app.py
import streamlit as st
from app_core import generate_itinerary, get_popular_destinations

# ------------------------------------------------------------------
# Pre-load destinations ------------------------------------------------
# Each item in destinations.json looks like {"name": "...", ... }
dest_names = [d["name"] for d in get_popular_destinations()]
dest_names.sort()            # nice UX: alphabetical

# ------------------------------------------------------------------
# UI ------------------------------------------------------------------
st.set_page_config(page_title="Travel-Itinerary-Pitcher", page_icon="✈️")
st.title("Travel-Itinerary-Pitcher ✈️")

prefs = {}

# Destination drop-down fed by JSON list
prefs["destination"] = st.selectbox(
    "Destination",
    dest_names,
    index=0 if dest_names else None,
    placeholder="Choose a destination…" if not dest_names else None,
)

# Other controls
prefs["interests"] = st.multiselect(
    "Interests",
    ["culture", "food", "nature", "nightlife", "history", "adventure"],
)
prefs["budget_level"] = st.selectbox(
    "Budget level",
    ["budget", "moderate", "luxury"],
)
prefs["trip_duration"] = st.slider("Duration (days)", 1, 14, 5)

# ------------------------------------------------------------------
# Action ------------------------------------------------------------
if st.button("Generate"):

    if not prefs["destination"]:
        st.warning("Please choose a destination first.")
        st.stop()

    with st.spinner("Cooking up your itinerary…"):
        result = generate_itinerary(prefs)

    st.success("Done!")
    st.header("Your trip narrative")
    st.write(result["narrative"]["main_narrative"])

    # Optional: show budget + day-by-day tabs
    with st.expander("Day-by-day itinerary"):
        for d in result["narrative"]["daily_plans"]:
            st.subheader(f"Day {d['day']}")
            st.write(d["content"])

    with st.expander("Budget breakdown"):
        st.write(result["narrative"]["budget_narrative"])
