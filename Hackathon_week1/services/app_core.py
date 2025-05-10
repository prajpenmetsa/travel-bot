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

# Third-party / internal services
from preference_service import PreferenceService
from location_service import LocationService
from experience_service import ExperienceService
from budget_service import BudgetService
from narrative_service import NarrativeService

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
        "OPENTRIPMAP_API_KEY": os.getenv("OPENTRIPMAP_API_KEY"),
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
    Core pipeline.

    Parameters
    ----------
    preferences : dict
        {
          "destination": str,
          "interests": List[str],
          "budget_level": str,
          "trip_duration": int
        }

    Returns
    -------
    dict
        The final narrative + budget so any UI can render or save it.
    """
    try:
        logger.info("Generating itinerary for %s", preferences["destination"])
        keys = load_api_keys()

        # Instantiate services
        loc_service = LocationService(api_key=keys["OPENTRIPMAP_API_KEY"])
        exp_service = ExperienceService(loc_service)
        bud_service = BudgetService()
        nar_service = NarrativeService(api_key=keys["GEMINI_API_KEY"])

        # Unpack prefs
        dest = preferences["destination"]
        ints = preferences["interests"]
        lvl = preferences["budget_level"]
        days = preferences["trip_duration"]

        # Pipeline
        exps = exp_service.suggest_experiences(dest, ints, lvl, days)
        budget = bud_service.calculate_budget(dest, ints, lvl, days)
        narrative = nar_service.generate_narrative(dest, ints, lvl, days, exps, budget)

        # CLI pretty-print (Streamlit can display differently)
        if os.getenv("RUN_CONTEXT", "CLI") == "CLI":
            _print_summary(dest, ints, lvl, days, narrative)

        return {"narrative": narrative, "budget": budget}

    except Exception as e:  # noqa: BLE001
        logger.exception("Failed to generate itinerary")
        raise RuntimeError(f"Unable to generate itinerary: {e}") from e
