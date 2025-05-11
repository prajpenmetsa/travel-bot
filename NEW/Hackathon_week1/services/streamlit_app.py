# streamlit_app.py
import json
import datetime as dt
from pathlib import Path

import streamlit as st
from app_core import generate_itinerary, get_popular_destinations, chat_with_itinerary, reset_chat_history


# ─────────────────────────────  PAGE CONFIG  ────────────────────────────────
st.set_page_config(page_title="Travel Itinerary Pitcher", page_icon="✈️", layout="wide")


# ─────────────────────────────  SESSION STATE  ──────────────────────────────
if "view_only" not in st.session_state:   # True when user opened a saved file
    st.session_state["view_only"] = False
if "last_prefs" not in st.session_state:
    st.session_state["last_prefs"] = None
if "last_result" not in st.session_state:
    st.session_state["last_result"] = None
if "chat_service" not in st.session_state:
    st.session_state["chat_service"] = None
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "itinerary"


# ─────────────────────────────  HELPERS  ────────────────────────────────────
SAVE_DIR = Path("saved_itineraries")
SAVE_DIR.mkdir(exist_ok=True)

def _save_itinerary(name: str, prefs: dict, result: dict) -> None:
    """Save only the serializable part of the result."""
    # Extract just the data part that's serializable
    if "data" in result:
        data_to_save = result["data"]
    else:
        # For backward compatibility, save everything except chat_service
        data_to_save = {k: v for k, v in result.items() if k != "chat_service"}
    
    serializable_data = {
        "prefs": prefs,
        "data": data_to_save
    }
    
    with (SAVE_DIR / f"{name}.json").open("w") as f:
        json.dump(serializable_data, f, indent=2)

def _list_saved() -> list[str]:
    return sorted(p.stem for p in SAVE_DIR.glob("*.json"))

def _load_itinerary(name: str) -> dict:
    with (SAVE_DIR / f"{name}.json").open() as f:
        return json.load(f)

def _render_itinerary(prefs: dict, result: dict) -> None:
    """Pretty-print an itinerary in the main panel."""
    st.header(f"🗺️  {prefs['destination'].title()} — {prefs['trip_duration']} days")
    st.write(result["narrative"]["main_narrative"])

    with st.expander("Day-by-day itinerary"):
        for d in result["narrative"]["daily_plans"]:
            st.write(d["content"])

    with st.expander("Budget breakdown"):
        st.write(result["narrative"]["budget_narrative"])


# ─────────────────────────────  SIDEBAR  ────────────────────────────────────
st.sidebar.header("📁 Saved itineraries")
saved_names = _list_saved()

sel_name = st.sidebar.selectbox("Open", saved_names) if saved_names else None
if sel_name and st.sidebar.button("Open"):
    loaded = _load_itinerary(sel_name)
    st.session_state["last_prefs"]  = loaded["prefs"]
    st.session_state["last_result"] = loaded["data"]
    st.session_state["view_only"]   = True
    # Reset chat service and history when loading a new itinerary
    st.session_state["chat_service"] = None
    st.session_state["chat_history"] = []
    st.toast(f"Loaded “{sel_name}”")
    st.rerun()                       # restart script so main panel updates

st.sidebar.markdown("---")

# Add chat controls to sidebar if we have an itinerary
if st.session_state["last_result"]:
    st.sidebar.header("💬 Chat Options")
    
    if st.sidebar.button("Reset Chat History"):
        if st.session_state["chat_service"]:
            reset_chat_history(st.session_state["chat_service"])
            st.session_state["chat_history"] = []
            st.toast("Chat history has been reset!")
    
    tab_options = ["itinerary", "chat"]
    selected_tab = st.sidebar.radio("View", tab_options, 
                                  index=tab_options.index(st.session_state["active_tab"]))
    if selected_tab != st.session_state["active_tab"]:
        st.session_state["active_tab"] = selected_tab
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("Files live in local 'saved_itineraries/'")


# ─────────────────────  VIEW-ONLY MODE (opened file)  ──────────────────────
if st.session_state["view_only"] and st.session_state["last_result"]:
    # Create tabs for itinerary and chat
    itinerary_tab, chat_tab = st.tabs(["🗺️ Itinerary", "💬 Chat with Assistant"])
    
    with itinerary_tab:
        _render_itinerary(st.session_state["last_prefs"],
                      st.session_state["last_result"])

        if st.button("🔄  Back to generator"):
            st.session_state["view_only"] = False
            st.rerun()
    
    with chat_tab:
        # Initialize chat service if needed
        if not st.session_state["chat_service"] and "chat_service" in st.session_state["last_result"]:
            st.session_state["chat_service"] = st.session_state["last_result"]["chat_service"]
        elif not st.session_state["chat_service"]:
            st.warning("Chat service is not available for this itinerary.")
            st.stop()
            
        st.subheader("💬 Chat with your Travel Assistant")
        st.info("Ask me anything about your itinerary! I can provide more details about attractions, restaurants, hotels, or answer any questions about your trip.")
        
        # Display chat history
        for message in st.session_state["chat_history"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        user_question = st.chat_input("Ask about your itinerary...")
        
        if user_question:
            # Add user message to chat history
            st.session_state["chat_history"].append({"role": "user", "content": user_question})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(user_question)
            
            # Get AI response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = chat_with_itinerary(st.session_state["chat_service"], user_question)
                st.markdown(response)
            
            # Add AI response to chat history
            st.session_state["chat_history"].append({"role": "assistant", "content": response})
            st.rerun()  # Update the UI with the new messages

    st.stop()           # nothing below runs while viewing a saved file


# ─────────────────────────────  MAIN UI FORM  ───────────────────────────────
dest_names = sorted(d["name"] for d in get_popular_destinations())

st.title("Travel-Itinerary-Pitcher ✈️")

prefs: dict = {}
prefs["destination"] = st.selectbox(
    "Destination",
    dest_names,
    index=0 if dest_names else None,
    placeholder="Choose a destination…" if not dest_names else None,
)
prefs["interests"] = st.multiselect(
    "Interests",
    ["culture", "food", "nature", "nightlife", "history", "adventure"],
)
prefs["budget_level"]  = st.selectbox("Budget level", ["budget", "moderate", "luxury"])
prefs["trip_duration"] = st.slider("Duration (days)", 1, 14, 5)


# ─────────────────────────────  GENERATE  ───────────────────────────────────
if st.button("Generate"):
    if not prefs["destination"]:
        st.warning("Please choose a destination first.")
        st.stop()

    with st.spinner("Cooking up your itinerary…"):
        result = generate_itinerary(prefs)
        
    # Store the chat service separately in session state
    if "chat_service" in result:
        st.session_state["chat_service"] = result["chat_service"]
        st.session_state["chat_history"] = []

    # Store the saveable data part
    if "data" in result:
        st.session_state["last_result"] = result["data"]
    else:
        # For backward compatibility
        st.session_state["last_result"] = result
        
    st.session_state["last_prefs"] = prefs
    st.session_state["view_only"] = False
    st.session_state["active_tab"] = "itinerary"
    st.rerun()                                 # refresh page with results


# ─────────────────────────────  SHOW RESULT  ────────────────────────────────
if st.session_state["last_result"]:
    # Create tabs for itinerary and chat
    itinerary_tab, chat_tab = st.tabs(["🗺️ Itinerary", "💬 Chat with Assistant"])
    
    # Set active tab based on sidebar selection
    if st.session_state["active_tab"] == "chat":
        chat_tab.active = True
    else:
        itinerary_tab.active = True
    
    with itinerary_tab:
        _render_itinerary(st.session_state["last_prefs"],
                      st.session_state["last_result"])
    
    with chat_tab:
        st.subheader("💬 Chat with your Travel Assistant")
        st.info("Ask me anything about your itinerary! I can provide more details about attractions, restaurants, hotels, or answer any questions about your trip.")
        
        # Display chat history
        for message in st.session_state["chat_history"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        user_question = st.chat_input("Ask about your itinerary...")
        
        if user_question:
            # Add user message to chat history
            st.session_state["chat_history"].append({"role": "user", "content": user_question})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(user_question)
            
            # Get AI response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = chat_with_itinerary(st.session_state["chat_service"], user_question)
                st.markdown(response)
            
            # Add AI response to chat history
            st.session_state["chat_history"].append({"role": "assistant", "content": response})
            st.rerun()  # Update the UI with the new messages


# ─────────────────────────────  SAVE SECTION  ───────────────────────────────
if not st.session_state["view_only"] and st.session_state["last_result"] and st.session_state["active_tab"] == "itinerary":
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
            st.success(f'Saved as "{fname}.json"')  # Fixed quotes
            st.rerun()                # refresh sidebar list
