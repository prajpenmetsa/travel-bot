"""
Travel Itinerary Pitcher - CLI Application
A command-line tool that generates personalized travel itineraries based on user preferences.
"""

import os
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import services
from preference_service import PreferenceService
from location_service import LocationService
from experience_service import ExperienceService
from budget_service import BudgetService
from narrative_service import NarrativeService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_api_keys() -> Dict[str, str]:
    """Load API keys from environment variables or config file"""
    keys = {
        "OPENTRIPMAP_API_KEY": os.environ.get("OPENTRIPMAP_API_KEY"),
        "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY")
    }
    
    # If keys not found in environment, try config file
    if not all(keys.values()):
        config_path = Path("config.json")
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                    for key in keys:
                        if not keys[key] and key in config:
                            keys[key] = config[key]
            except Exception as e:
                logger.error(f"Error loading config file: {e}")
    
    missing_keys = [k for k, v in keys.items() if not v]
    if missing_keys:
        logger.warning(f"Missing API keys: {', '.join(missing_keys)}")
    
    return keys

def get_popular_destinations() -> List[Dict[str, Any]]:
    """Get list of popular destinations from destinations.json"""
    try:
        with open("data/destinations.json", "r") as f:
            data = json.load(f)
            return data.get("popular_destinations", [])
    except Exception as e:
        logger.error(f"Error loading destinations: {e}")
        return []

def display_trip_summary(
    destination: str,
    interests: List[str],
    budget_level: str,
    trip_duration: int,
    narrative: Dict[str, Any],
    budget: Dict[str, Any]
) -> None:
    """Display trip summary in a formatted way"""
    print("\n" + "="*80)
    print(f"YOUR {trip_duration}-DAY {budget_level.upper()} ADVENTURE IN {destination.upper()}")
    print("="*80 + "\n")
    
    # Print main narrative
    print(narrative["main_narrative"])
    print("\n" + "-"*80 + "\n")
    
    # Print daily plans
    print("## DAY-BY-DAY ITINERARY\n")
    for day_plan in narrative["daily_plans"]:
        print(f"### DAY {day_plan['day']}")
        print(day_plan["content"])
        print()
    
    print("-"*80 + "\n")
    
    # Print budget breakdown
    print("## BUDGET BREAKDOWN\n")
    print(narrative["budget_narrative"])
    print("\n" + "="*80)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Travel Itinerary Pitcher CLI')
    
    parser.add_argument('--destination', '-d', type=str, help='Destination city or country')
    parser.add_argument('--interests', '-i', type=str, nargs='+', 
                        choices=PreferenceService.VALID_INTERESTS,
                        help='Interests (space-separated)')
    parser.add_argument('--budget', '-b', type=str,
                        choices=PreferenceService.VALID_BUDGET_LEVELS,
                        help='Budget level: budget, moderate, or luxury')
    parser.add_argument('--duration', '-t', type=int,
                        help='Trip duration in days (1-14)')
    parser.add_argument('--interactive', '-int', action='store_true',
                        help='Run in interactive mode')
    
    return parser.parse_args()

def interactive_mode() -> Dict[str, Any]:
    """Run application in interactive mode"""
    print("\n===== WELCOME TO TRAVEL ITINERARY PITCHER =====\n")
    
    # Get popular destinations for reference
    popular_destinations = get_popular_destinations()
    destination_names = [dest["name"] for dest in popular_destinations]
    
    # Show some popular destinations
    print("Some popular destinations:")
    for i, name in enumerate(destination_names[:10]):
        print(f"  - {name}")
    print()
    
    # Get destination
    while True:
        destination = input("Enter your destination (city or country): ").strip()
        try:
            destination = PreferenceService.validate_destination(destination)
            break
        except ValueError as e:
            print(f"Error: {e}")
    
    # Get interests
    print(f"\nAvailable interest categories: {', '.join(PreferenceService.VALID_INTERESTS)}")
    while True:
        interests_input = input("Enter your interests (comma-separated): ").strip()
        interests = [i.strip().lower() for i in interests_input.split(",")]
        try:
            interests = PreferenceService.validate_interests(interests)
            break
        except ValueError as e:
            print(f"Error: {e}")
    
    # Get budget level
    print(f"\nBudget levels: {', '.join(PreferenceService.VALID_BUDGET_LEVELS)}")
    while True:
        budget_level = input("Enter your budget level: ").strip().lower()
        try:
            budget_level = PreferenceService.validate_budget_level(budget_level)
            break
        except ValueError as e:
            print(f"Error: {e}")
    
    # Get trip duration
    while True:
        try:
            trip_duration = int(input("\nEnter trip duration (days, 1-14): "))
            trip_duration = PreferenceService.validate_trip_duration(trip_duration)
            break
        except (ValueError, TypeError) as e:
            print(f"Error: {e}")
    
    return {
        "destination": destination,
        "interests": interests,
        "budget_level": budget_level,
        "trip_duration": trip_duration
    }

def generate_itinerary(preferences: Dict[str, Any]) -> None:
    """Generate and display travel itinerary"""
    try:
        print("\nGenerating your personalized travel itinerary...\n")
        
        # Load API keys
        api_keys = load_api_keys()
        
        # Initialize services
        location_service = LocationService(api_key=api_keys["OPENTRIPMAP_API_KEY"])
        experience_service = ExperienceService(location_service)
        budget_service = BudgetService()
        narrative_service = NarrativeService(api_key=api_keys["GEMINI_API_KEY"])
        
        # Extract preference values
        destination = preferences["destination"]
        interests = preferences["interests"]
        budget_level = preferences["budget_level"]
        trip_duration = preferences["trip_duration"]
        
        # Generate experiences
        print("Finding experiences that match your interests...")
        experiences = experience_service.suggest_experiences(
            destination, interests, budget_level, trip_duration
        )
        
        # Calculate budget
        print("Calculating budget estimates...")
        budget = budget_service.calculate_budget(
            destination, interests, budget_level, trip_duration
        )
        
        # Generate narrative
        print("Creating your personalized travel narrative...")
        narrative = narrative_service.generate_narrative(
            destination, interests, budget_level, trip_duration, experiences, budget
        )
        
        # Display results
        display_trip_summary(
            destination, interests, budget_level, trip_duration, narrative, budget
        )
        
        # Save results if user wants
        save = input("\nDo you want to save this itinerary? (y/n): ").strip().lower()
        if save == 'y' or save == 'yes':
            filename = f"itinerary_{destination.replace(' ', '_')}_{trip_duration}days.md"
            with open(filename, 'w') as f:
                f.write(f"# {trip_duration}-DAY {budget_level.upper()} ADVENTURE IN {destination.upper()}\n\n")
                f.write(narrative["main_narrative"])
                f.write("\n\n## DAY-BY-DAY ITINERARY\n\n")
                for day_plan in narrative["daily_plans"]:
                    f.write(f"### DAY {day_plan['day']}\n")
                    f.write(day_plan["content"])
                    f.write("\n\n")
                f.write("\n## BUDGET BREAKDOWN\n\n")
                f.write(narrative["budget_narrative"])
            print(f"\nItinerary saved to {filename}")
        
    except Exception as e:
        logger.error(f"Error generating itinerary: {e}")
        print(f"\nError: Unable to generate itinerary. {str(e)}")

def main():
    """Main application function"""
    args = parse_args()
    
    # Run in interactive mode if specified or no arguments provided
    if args.interactive or not (args.destination and args.interests and args.budget and args.duration):
        preferences = interactive_mode()
    else:
        # Use command line arguments
        preferences = {
            "destination": args.destination,
            "interests": args.interests,
            "budget_level": args.budget,
            "trip_duration": args.duration
        }
    
    # Generate itinerary
    generate_itinerary(preferences)

if __name__ == "__main__":
    main()