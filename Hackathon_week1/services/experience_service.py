"""
Experience Service - Handles suggesting activities and experiences based on user preferences.
"""

from typing import List, Dict, Any
import random
from location_service import LocationService

class ExperienceService:
    """Service for suggesting experiences based on preferences"""
    
    def __init__(self, location_service: LocationService):
        """Initialize with location service"""
        self.location_service = location_service
    
    def suggest_experiences(self, 
                          destination: str,
                          interests: List[str], 
                          budget_level: str,
                          trip_duration: int) -> Dict[str, Any]:
        """Suggest experiences for the trip based on user preferences"""
        # Get points of interest from location service
        pois = self.location_service.get_points_of_interest(
            destination, interests, limit=trip_duration * 3  # Get more POIs than days
        )
        
        # Group POIs by types aligned with interests
        grouped_pois = self._group_pois_by_interest(pois, interests)
        
        # Create a day-by-day plan
        daily_plans = self._create_daily_plans(
            grouped_pois, trip_duration, destination, interests, budget_level
        )
        
        return {
            "points_of_interest": pois,
            "daily_plans": daily_plans
        }
    
    def _group_pois_by_interest(self, pois: List[Dict[str, Any]], interests: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Group POIs by interest category"""
        # Map POI kinds to interests
        kind_to_interest = {
            "historic": "history",
            "museums": "history",
            "archaeology": "history",
            "architecture": "history",
            "religion": "history",
            "foods": "food",
            "restaurants": "food",
            "cafes": "food",
            "breweries": "food",
            "wineries": "food",
            "sport": "adventure",
            "amusements": "adventure",
            "natural": "nature",
            "cultural": "culture",
            "theatres_and_entertainments": "culture",
            "beaches": "relaxation",
            "gardens": "relaxation",
            "spas": "relaxation",
            "parks": "nature",
            "commercial": "shopping",
            "shops": "shopping",
            "malls": "shopping",
            "bars": "nightlife",
            "casinos": "nightlife",
            "zoos": "family"
        }
        
        grouped = {interest: [] for interest in interests}
        
        # Add each POI to appropriate interest groups
        for poi in pois:
            for kind in poi.get("kinds", []):
                if kind in kind_to_interest and kind_to_interest[kind] in interests:
                    interest = kind_to_interest[kind]
                    if poi not in grouped[interest]:
                        grouped[interest].append(poi)
        
        return grouped
    
    def _create_daily_plans(self, 
                          grouped_pois: Dict[str, List[Dict[str, Any]]],
                          trip_duration: int,
                          destination: str,
                          interests: List[str],
                          budget_level: str) -> List[Dict[str, Any]]:
        """Create a day-by-day plan for the trip"""
        daily_plans = []
        
        # Ensure we have at least one POI for each day
        if sum(len(pois) for pois in grouped_pois.values()) < trip_duration:
            # If we don't have enough POIs, we'll create some generic activities
            generic_activities = self._generate_generic_activities(
                destination, interests, trip_duration
            )
        else:
            generic_activities = []
        
        # Assign primary interest/theme for each day
        day_themes = []
        
        # First, use each interest at least once if we have enough days
        for interest in interests[:min(len(interests), trip_duration)]:
            day_themes.append(interest)
        
        # Fill remaining days with random interests
        while len(day_themes) < trip_duration:
            day_themes.append(random.choice(interests))
        
        # Shuffle day themes for variety
        random.shuffle(day_themes)
        
        # Create a plan for each day
        for day in range(1, trip_duration + 1):
            theme = day_themes[day - 1]
            
            # Get POIs for the day's theme
            theme_pois = grouped_pois.get(theme, [])
            
            # Select 1-2 POIs for this day if available
            day_pois = []
            if theme_pois:
                day_pois = random.sample(
                    theme_pois, 
                    min(2, len(theme_pois))
                )
                # Remove selected POIs to avoid duplicates
                for poi in day_pois:
                    if poi in theme_pois:
                        theme_pois.remove(poi)
            
            # Add generic activities if we don't have enough POIs
            if not day_pois and generic_activities:
                day_pois = [generic_activities.pop() for _ in range(min(2, len(generic_activities)))]
            
            # Create the day plan
            day_plan = {
                "day": day,
                "theme": theme,
                "activities": day_pois
            }
            
            daily_plans.append(day_plan)
        
        return daily_plans
    
    def _generate_generic_activities(self, 
                                   destination: str,
                                   interests: List[str],
                                   count: int) -> List[Dict[str, Any]]:
        """Generate generic activities when not enough POIs are available"""
        generic_templates = {
            "history": [
                {"name": f"Visit {destination} Historical Sites", "kinds": ["historic"]},
                {"name": f"Guided Tour of {destination}'s History", "kinds": ["historic"]},
                {"name": f"Explore {destination} Architecture", "kinds": ["architecture"]}
            ],
            "food": [
                {"name": f"Food Tour in {destination}", "kinds": ["foods"]},
                {"name": f"Cooking Class with {destination} Cuisine", "kinds": ["foods"]},
                {"name": f"Discover Local Food Market in {destination}", "kinds": ["foods"]}
            ],
            "adventure": [
                {"name": f"Outdoor Adventure in {destination}", "kinds": ["sport"]},
                {"name": f"Hiking near {destination}", "kinds": ["sport"]},
                {"name": f"Water Activities in {destination}", "kinds": ["sport"]}
            ],
            "culture": [
                {"name": f"Cultural Tour of {destination}", "kinds": ["cultural"]},
                {"name": f"Attend Local Performance in {destination}", "kinds": ["theatres_and_entertainments"]},
                {"name": f"Art Exploration in {destination}", "kinds": ["cultural"]}
            ],
            "nature": [
                {"name": f"Nature Walk in {destination}", "kinds": ["natural"]},
                {"name": f"Visit {destination} Parks", "kinds": ["parks"]},
                {"name": f"Scenic Views in {destination}", "kinds": ["natural"]}
            ],
            "relaxation": [
                {"name": f"Spa Day in {destination}", "kinds": ["spas"]},
                {"name": f"Relax at {destination} Gardens", "kinds": ["gardens"]},
                {"name": f"Wellness Activities in {destination}", "kinds": ["spas"]}
            ],
            "shopping": [
                {"name": f"Shopping in {destination}", "kinds": ["shops"]},
                {"name": f"Find Local Souvenirs in {destination}", "kinds": ["shops"]},
                {"name": f"Artisan Shopping in {destination}", "kinds": ["shops"]}
            ],
            "nightlife": [
                {"name": f"Night Tour of {destination}", "kinds": ["bars"]},
                {"name": f"Discover {destination} Nightlife", "kinds": ["bars"]},
                {"name": f"Evening Entertainment in {destination}", "kinds": ["theatres_and_entertainments"]}
            ],
            "family": [
                {"name": f"Family Fun in {destination}", "kinds": ["amusements"]},
                {"name": f"Kid-Friendly Activities in {destination}", "kinds": ["amusements"]},
                {"name": f"Family Adventure in {destination}", "kinds": ["amusements"]}
            ]
        }
        
        # Generate activities for each interest
        activities = []
        for interest in interests:
            if interest in generic_templates:
                activities.extend(generic_templates[interest])
        
        # Shuffle and return requested number
        random.shuffle(activities)
        return activities[:count]