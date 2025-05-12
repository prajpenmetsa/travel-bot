"""
Core logic for Travel-Itinerary-Pitcher.

Anything that a UI (CLI, Streamlit, FastAPI, etc.) might need is kept here so
it can simply `import app_core` and call `generate_itinerary()`.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from functools import lru_cache

# Third-party / internal services
from preference_service import PreferenceService
from location_service import LocationService
from experience_service import ExperienceService
from budget_service import BudgetService
from narrative_service import NarrativeService
from evaluation_service import EvaluationService
from itinerary_chat_service import ItineraryChatService

# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Helpers (API keys, destination list, pretty printer)
# ------------------------------------------------------------------------------
def load_api_keys() -> Dict[str, str]:
    """Return a dict with all API keys, trying ENV first and then config.json."""
    keys = {
        "FOURSQUARE_API_KEY": os.getenv("FOURSQUARE_API_KEY"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
    }

    if not all(keys.values()):
        cfg = Path("config.json")
        if cfg.exists():
            try:
                with cfg.open() as f:
                    data = json.load(f)
                for k in keys:
                    keys[k] = keys[k] or data.get(k)
            except Exception as e:  # noqa: BLE001
                logger.error("Error reading config.json: %s", e)

    missing = [k for k, v in keys.items() if not v]
    if missing:
        logger.warning("Missing API keys: %s", ", ".join(missing))

    return keys


def get_popular_destinations() -> List[Dict[str, Any]]:
    """Read the bundled destinations.json (three fallback paths)."""
    try:
        root = Path(__file__).resolve().parent
        candidates = [
            root / "data" / "destinations.json",
            root.parent / "services" / "data" / "destinations.json",
            Path(
                "/Users/lakshmiprajnapenmetsa/Desktop/iiith/research/travel-bot/"
                "travel-bot/Hackathon_week1/services/data/destinations.json"
            ),
        ]
        for p in candidates:
            if p.exists():
                with p.open() as f:
                    return json.load(f).get("popular_destinations", [])
        raise FileNotFoundError("destinations.json not found in any known path.")
    except Exception as e:  # noqa: BLE001
        logger.error("Error loading destinations: %s", e)
        return []


def _print_summary(
    destination: str,
    interests: List[str],
    budget_level: str,
    trip_duration: int,
    narrative: Dict[str, Any],
) -> None:
    """Pretty printer for terminal / Markdown outputs."""
    line = "=" * 80
    print("\n" + line)
    print(f"YOUR {trip_duration}-DAY {budget_level.upper()} ADVENTURE IN {destination.upper()}")
    print(line + "\n")

    print(narrative["main_narrative"])
    print("\n" + "-" * 80 + "\n")

    print("## DAY-BY-DAY ITINERARY\n")
    for d in narrative["daily_plans"]:
        print(f"### DAY {d['day']}")
        print(d["content"], end="\n\n")

    print("-" * 80 + "\n")
    print("## BUDGET BREAKDOWN\n")
    print(narrative["budget_narrative"])
    print("\n" + line)

# ------------------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------------------
def generate_itinerary(preferences: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build itinerary, budget, quality score **and** initialise an AI chat session.

    Returns
    -------
    dict
        {
          "narrative": …,
          "budget":    …,
          "scores":    …,
          "chat_id":   str | None
        }
    """
    try:
        logger.info("Generating itinerary for %s", preferences["destination"])
        keys = load_api_keys()

        # ─── Instantiate services ───────────────────────────────────────────
        loc_service  = LocationService(api_key=keys["FOURSQUARE_API_KEY"])
        exp_service  = ExperienceService(loc_service)
        bud_service  = BudgetService()
        nar_service  = NarrativeService(api_key=keys["GEMINI_API_KEY"])
        eval_service = EvaluationService()
        chat_service = ItineraryChatService(api_key=keys["GEMINI_API_KEY"])

        # ─── Unpack prefs ───────────────────────────────────────────────────
        dest  = preferences["destination"]
        ints  = preferences["interests"]
        lvl   = preferences["budget_level"]
        days  = preferences["trip_duration"]

        # ─── Core pipeline ──────────────────────────────────────────────────
        exps = exp_service.suggest_experiences(dest, ints, lvl, days)
        raw_budget = bud_service.calculate_budget(dest, ints, lvl, days)
        
        # Convert exps list to a dictionary if it's a list
        experiences_dict = {"points_of_interest": exps} if isinstance(exps, list) else exps
        
        # Format budget as expected by other services
        if isinstance(raw_budget, (int, float)):
            budget = {
                "total": {
                    "grand_total": raw_budget
                },
                "per_day": {
                    "total_daily": raw_budget / days
                }
            }
        elif isinstance(raw_budget, dict) and "total" in raw_budget and isinstance(raw_budget["total"], (int, float)):
            budget = {
                "total": {
                    "grand_total": raw_budget["total"]
                },
                "per_day": {
                    "total_daily": raw_budget["total"] / days
                }
            }
        else:
            budget = raw_budget

        # Log the budget type and format for debugging
        logger.info(f"Budget type: {type(budget)}, format: {budget}")
        
        narrative = nar_service.generate_narrative(dest, ints, lvl, days, experiences_dict, budget)
        scores = eval_service.score(preferences, narrative, budget)

        # ─── Initialise chat session (robust to method name) ────────────────
        chat_id = None
        if chat_service:
            logger.info(f"API key available for chat: {bool(keys.get('GEMINI_API_KEY'))}")
            
            if hasattr(chat_service, "start_session"):
                chat_id = chat_service.start_session(
                    destination=dest,
                    interests=ints,
                    budget_level=lvl,
                    trip_duration=days,
                    narrative=narrative,
                    budget=budget,
                    experiences=exps,
                    scores=scores,
                )
            elif hasattr(chat_service, "create_session"):
                chat_id = chat_service.create_session(
                    prefs=preferences,
                    narrative=narrative,
                    budget=budget,
                    experiences=exps,
                    scores=scores,
                )
                
                # Store in the cache if successfully created
                if chat_id:
                    _CHAT_SERVICES[chat_id] = chat_service
                    logger.info(f"Chat service stored in cache with ID {chat_id}")
            else:
                logger.warning(
                    "ItineraryChatService has no start_session/create_session; chat disabled."
                )

        # ─── CLI pretty-print (optional) ────────────────────────────────────
        if os.getenv("RUN_CONTEXT", "CLI") == "CLI":
            _print_summary(dest, ints, lvl, days, narrative)
            print(f"\n★ Planner quality score: {scores['total']}/100")
            if chat_id:
                print(f"(Chat session id: {chat_id})")
            print()

        return {
            "narrative": narrative,
            "budget":    budget,
            "scores":    scores,
            "chat_id":   chat_id,
        }

    except Exception as e:                        # noqa: BLE001
        logger.exception("Failed to generate itinerary")
        raise RuntimeError(f"Unable to generate itinerary: {e}") from e


# ------------------------------------------------------------------------------
# Follow-up Q&A
# ------------------------------------------------------------------------------
_CHAT_SERVICES = {}

def ask_itinerary_chat(chat_id: str, user_message: str) -> str:
    """
    Relay a user question to the existing itinerary chat session and
    return the AI's answer.
    """
    global _CHAT_SERVICES
    keys = load_api_keys()
    
    if not keys.get("GEMINI_API_KEY"):
        return "I apologize, but the chat functionality is not available because the Gemini API key is missing."

    # Use cached chat service if available, otherwise create new one
    if chat_id in _CHAT_SERVICES:
        logger.info(f"Using existing chat service for session {chat_id}")
        chat_service = _CHAT_SERVICES[chat_id]
    else:
        logger.info(f"Creating new chat service for session {chat_id}")
        chat_service = ItineraryChatService(api_key=keys["GEMINI_API_KEY"])
        _CHAT_SERVICES[chat_id] = chat_service
    
    try:
        return chat_service.answer(chat_id, user_message)
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return f"I encountered an error while processing your question. Please try again later."


