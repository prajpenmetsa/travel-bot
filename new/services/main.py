"""
CLI entry-point for Travel-Itinerary-Pitcher.

Keeps only user interaction & argument parsing.
Everything else resides in app_core.py so other frontends can reuse it.
"""

import argparse
from typing import Dict, Any, List

from preference_service import PreferenceService
from app_core import (
    generate_itinerary,      # core pipeline
    get_popular_destinations # helper for interactive prompt
)

# ------------------------------------------------------------------------------
# CLI helpers
# ------------------------------------------------------------------------------
def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Travel Itinerary Pitcher CLI")

    p.add_argument("-d", "--destination", type=str, help="City or country")
    p.add_argument(
        "-i", "--interests",
        nargs="+",
        choices=PreferenceService.VALID_INTERESTS,
        help="Interests (space-separated)"
    )
    p.add_argument(
        "-b", "--budget",
        choices=PreferenceService.VALID_BUDGET_LEVELS,
        help="budget | moderate | luxury"
    )
    p.add_argument("-t", "--duration", type=int, help="Trip length (1-14 days)")
    p.add_argument("-int", "--interactive", action="store_true",
                   help="Ignore flags and ask questions interactively")
    return p.parse_args()


def _interactive_prompt() -> Dict[str, Any]:
    print("\n===== WELCOME TO TRAVEL ITINERARY PITCHER =====\n")

    # Suggest a few popular places
    for name in [d["name"] for d in get_popular_destinations()[:10]]:
        print(f"  • {name}")
    print()

    # Destination
    while True:
        try:
            dest = PreferenceService.validate_destination(
                input("Destination (city/country): ").strip()
            )
            break
        except ValueError as e:
            print(f"Error: {e}")

    # Interests
    print(f"\nChoose interests: {', '.join(PreferenceService.VALID_INTERESTS)}")
    while True:
        try:
            ints = PreferenceService.validate_interests(
                [s.strip() for s in input("Interests (comma-separated): ").split(",")]
            )
            break
        except ValueError as e:
            print(f"Error: {e}")

    # Budget
    print(f"\nBudget levels: {', '.join(PreferenceService.VALID_BUDGET_LEVELS)}")
    while True:
        try:
            lvl = PreferenceService.validate_budget_level(
                input("Budget level: ").strip().lower()
            )
            break
        except ValueError as e:
            print(f"Error: {e}")

    # Duration
    while True:
        try:
            days = PreferenceService.validate_trip_duration(
                int(input("\nTrip duration (1-14): "))
            )
            break
        except (ValueError, TypeError) as e:
            print(f"Error: {e}")

    return {"destination": dest, "interests": ints, "budget_level": lvl, "trip_duration": days}


# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------
def main() -> None:
    args = _parse_args()

    # Decide interactive vs flags
    if args.interactive or not (args.destination and args.interests and args.budget and args.duration):
        prefs = _interactive_prompt()
    else:
        prefs: Dict[str, Any] = {
            "destination": args.destination,
            "interests": args.interests,
            "budget_level": args.budget,
            "trip_duration": args.duration,
        }

    # Run pipeline
    generate_itinerary(prefs)


if __name__ == "__main__":
    main()
