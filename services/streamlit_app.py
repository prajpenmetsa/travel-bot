# streamlit_app.py
import json
import datetime as dt
from pathlib import Path

import streamlit as st
from app_core import (
    generate_itinerary,
    get_popular_destinations,
    ask_itinerary_chat,      # NEW
)

# ─────────────────────────────  PAGE CONFIG  ────────────────────────────────
st.set_page_config(page_title="Travel Itinerary Pitcher", page_icon="✈️")

# ─────────────────────────────  SESSION STATE  ──────────────────────────────
defaults = {
    "view_only": False,
    "last_prefs": None,
    "last_result": None,
    "chat_id": None,
    "chat_history": [],      # list[tuple[str,str]]  (role, message)
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

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
    """Pretty-print an itinerary + score + chat panel."""
    st.header(f"🗺️  {prefs['destination'].title()} — {prefs['trip_duration']} days")
    st.write(result["narrative"]["main_narrative"])

    with st.expander("In-depth itinerary"):
        for d in result["narrative"]["daily_plans"]:
            st.write(d["content"])

    with st.expander("Budget breakdown"):
        st.write(result["narrative"]["budget_narrative"])

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

    # ─── Chat panel ─────────────────────────────────────────────────────────
    chat_id = result.get("chat_id") or st.session_state.get("chat_id")
    
    if chat_id:
        st.markdown("---")
        st.subheader("💬 Ask the itinerary AI")

        # Display history
        for role, msg in st.session_state.chat_history:
            st.chat_message(role).write(msg)

        user_msg = st.chat_input("Ask a question about this trip…")
        if user_msg:
            st.session_state.chat_history.append(("user", user_msg))
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        reply = ask_itinerary_chat(chat_id, user_msg)
                        if "not available" in reply or "error" in reply.lower():
                            st.error("There was an issue connecting to the chat service.")
                            st.info("This could be due to API key issues or service limitations.")
                            reply = "I'm sorry, but I'm having trouble accessing information about your itinerary right now."
                        st.write(reply)
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                        reply = "Sorry, I encountered an error while processing your request."
                        st.write(reply)
            st.session_state.chat_history.append(("assistant", reply))

# ─────────────────────────────  SIDEBAR  ────────────────────────────────────
st.sidebar.header("📁 Saved itineraries")
saved_names = _list_saved()

sel_name = st.sidebar.selectbox("Open", saved_names) if saved_names else None
if sel_name and st.sidebar.button("Open"):
    loaded = _load_itinerary(sel_name)
    st.session_state["last_prefs"]  = loaded["prefs"]
    st.session_state["last_result"] = loaded["data"]
    st.session_state["chat_id"]     = loaded["data"].get("chat_id")
    st.session_state["chat_history"] = []
    st.session_state["view_only"]   = True
    st.toast(f"Loaded “{sel_name}”")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("Files live in local ‘saved_itineraries/’")

# ─────────────────────  VIEW-ONLY MODE  ─────────────────────────────────────
if st.session_state["view_only"] and st.session_state["last_result"]:
    _render_itinerary(st.session_state["last_prefs"],
                      st.session_state["last_result"])

    if st.button("🔄  Back to generator"):
        st.session_state["view_only"] = False
        st.session_state["chat_history"] = []
        st.rerun()

    st.stop()

# ─────────────────────────────  MAIN UI FORM  ───────────────────────────────
dest_choices = sorted(d["name"] for d in get_popular_destinations())
dest_choices.append("Other…")

st.title("Travel-Itinerary-Pitcher ✈️")

prefs: dict = {}

chosen = st.selectbox(
    "Destination",
    dest_choices,
    index=0 if dest_choices else None,
    placeholder="Choose a destination…" if not dest_choices else None,
)
prefs["destination"] = st.text_input("Type your destination") if chosen == "Other…" else chosen

prefs["interests"] = st.multiselect(
    "Interests",
    ["culture", "food", "nature", "nightlife", "history", "adventure"],
)
prefs["budget_level"] = st.selectbox("Budget level", ["budget", "moderate", "luxury"])
prefs["trip_duration"] = st.slider("Duration (days)", 1, 14, 5)

# ─────────────────────────────  GENERATE  ───────────────────────────────────
if st.button("Generate"):
    if not prefs["destination"].strip():
        st.warning("Please choose or type a destination first.")
        st.stop()

    with st.spinner("Cooking up your itinerary…"):
        result = generate_itinerary(prefs)

    st.session_state["last_prefs"]   = prefs
    st.session_state["last_result"]  = result
    st.session_state["chat_id"]      = result.get("chat_id")
    st.session_state["chat_history"] = []
    st.session_state["view_only"]    = False
    st.rerun()

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
            st.rerun()

# Add this near the top after imports
if st.sidebar.checkbox("Debug Mode"):
    st.sidebar.subheader("API Key Status")
    from app_core import load_api_keys
    keys = load_api_keys()
    
    st.sidebar.write(f"Gemini API key: {'✓ Present' if keys.get('GEMINI_API_KEY') else '✗ Missing'}")
    st.sidebar.write(f"Foursquare API key: {'✓ Present' if keys.get('FOURSQUARE_API_KEY') else '✗ Missing'}")
    
    st.sidebar.subheader("Session State")
    st.sidebar.write(f"Chat ID: {st.session_state.get('chat_id')}")
    
    if st.session_state.get('chat_id') and st.sidebar.button("Test Chat Direct"):
        from itinerary_chat_service import ItineraryChatService
        chat_service = ItineraryChatService(api_key=keys.get("GEMINI_API_KEY"))
        try:
            response = chat_service.chat("Hello, can you respond with a test message?")
            st.sidebar.success("Direct chat test successful!")
            st.sidebar.write(response)
        except Exception as e:
            st.sidebar.error(f"Direct chat test failed: {str(e)}")
