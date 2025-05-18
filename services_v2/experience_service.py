"""
Experience Service - Handles suggesting activities and experiences based on user preferences.
"""

from typing import List, Dict, Any
import random
from location_service import LocationService

class ExperienceService:
    """Service for suggesting travel experiences and activities."""
    
    def __init__(self, location_service: LocationService):
        """
        Initialize the experience service.
        
        Parameters:
        -----------
        location_service : LocationService
            An instance of the LocationService for venue lookups
        """
        self.location_service = location_service
        
        # Default experiences by interest category
        self.default_experiences = {
            "food": [
                {"name": "Local Food Tour", "type": "food", "cost": 40, "duration": 3.0},
                {"name": "Cooking Class", "type": "food", "cost": 60, "duration": 2.5}
            ],
            "history": [
                {"name": "Museum Visit", "type": "culture", "cost": 15, "duration": 2.0},
                {"name": "Historical Walking Tour", "type": "tour", "cost": 25, "duration": 2.5}
            ],
            "art": [
                {"name": "Art Gallery", "type": "culture", "cost": 12, "duration": 1.5},
                {"name": "Street Art Tour", "type": "tour", "cost": 20, "duration": 2.0}
            ],
            "nature": [
                {"name": "Park Exploration", "type": "outdoors", "cost": 0, "duration": 2.0},
                {"name": "Botanical Garden", "type": "outdoors", "cost": 10, "duration": 1.5}
            ],
            "adventure": [
                {"name": "Hiking Trip", "type": "outdoors", "cost": 35, "duration": 4.0},
                {"name": "Water Activities", "type": "outdoors", "cost": 50, "duration": 3.0}
            ],
            "relaxation": [
                {"name": "Spa Treatment", "type": "wellness", "cost": 80, "duration": 2.0},
                {"name": "Beach Day", "type": "outdoors", "cost": 10, "duration": 4.0}
            ],
            "shopping": [
                {"name": "Local Market", "type": "shopping", "cost": 0, "duration": 2.0},
                {"name": "Shopping District", "type": "shopping", "cost": 0, "duration": 3.0}
            ]
        }
        
        # Special experiences by destination
        self.destination_experiences = {
            "Paris": [
                {"name": "Eiffel Tower", "type": "landmark", "cost": 25, "duration": 2.0},
                {"name": "Louvre Museum", "type": "museum", "cost": 15, "duration": 3.0},
                {"name": "Seine River Cruise", "type": "cruise", "cost": 30, "duration": 1.5}
            ],
            "Tokyo": [
                {"name": "Senso-ji Temple", "type": "temple", "cost": 0, "duration": 1.5},
                {"name": "Tsukiji Outer Market", "type": "market", "cost": 0, "duration": 2.0},
                {"name": "Shibuya Crossing", "type": "landmark", "cost": 0, "duration": 0.5}
            ],
            "New York": [
                {"name": "Central Park", "type": "park", "cost": 0, "duration": 2.0},
                {"name": "Metropolitan Museum of Art", "type": "museum", "cost": 25, "duration": 3.0},
                {"name": "Broadway Show", "type": "entertainment", "cost": 120, "duration": 3.0}
            ]
        }
    
    def suggest_experiences(self, 
                          destination: str,
                          interests: List[str], 
                          budget_level: str,
                          trip_duration: int) -> List[Dict[str, Any]]:
        """Suggest travel experiences based on preferences"""
        suggested = []
        
        # First add destination-specific experiences
        if destination in self.destination_experiences:
            suggested.extend(self.destination_experiences[destination])
        
        # Then add experiences based on interests
        for interest in interests:
            if interest in self.default_experiences:
                suggested.extend(self.default_experiences[interest])
        
        # If we have a location service with venues, add those
        if self.location_service:
            try:
                venue_categories = self._map_interests_to_venue_categories(interests)
                venues = self.location_service.search_venues(
                    destination=destination,
                    categories=venue_categories,
                    limit=10
                )
                
                # Convert venue data to experience format
                for venue in venues:
                    # Skip if already included
                    if any(e.get("name") == venue.get("name") for e in suggested):
                        continue
                        
                    # Map venue category to experience type
                    experience_type = "activity"
                    if "categories" in venue and venue["categories"]:
                        cat_name = venue["categories"][0]["name"].lower()
                        if "museum" in cat_name or "gallery" in cat_name:
                            experience_type = "museum"
                        elif "restaurant" in cat_name or "cafe" in cat_name:
                            experience_type = "food"
                        elif "landmark" in cat_name or "monument" in cat_name:
                            experience_type = "landmark"
                        
                    # Estimate cost based on budget level
                    cost = 15  # default
                    if budget_level == "low":
                        cost = 10
                    elif budget_level == "medium":
                        cost = 20
                    elif budget_level == "high":
                        cost = 40
                    
                    suggested.append({
                        "name": venue.get("name", "Local Venue"),
                        "type": experience_type,
                        "cost": cost,
                        "duration": 1.5,  # default duration
                        "source": "venue"
                    })
            except Exception as e:
                print(f"Error fetching venue data: {e}")
        
        # Filter or adjust based on budget level
        suggested = self._filter_by_budget(suggested, budget_level)
        
        # Ensure sufficient experiences for the trip duration
        # As a rule of thumb, we need 2-3 experiences per day
        min_required = trip_duration * 2
        while len(suggested) < min_required:
            # Add more generic experiences
            suggested.extend([
                {"name": "Local Restaurant", "type": "food", "cost": 20, "duration": 1.5},
                {"name": "City Walk", "type": "activity", "cost": 0, "duration": 1.0},
                {"name": "Local Cafe", "type": "food", "cost": 10, "duration": 1.0}
            ])
            
        return suggested
    
    def _map_interests_to_venue_categories(self, interests):
        """
        Map interest categories to venue API categories.
        
        Parameters:
        -----------
        interests : list
            List of interest categories
            
        Returns:
        --------
        list
            List of venue API category IDs
        """
        # Mapping from interests to Foursquare category IDs
        # In a real implementation, these would be actual Foursquare category IDs
        mapping = {
            "food": ["restaurant", "cafe"],
            "history": ["historic site", "museum"],
            "art": ["art gallery", "museum"],
            "nature": ["park", "garden"],
            "shopping": ["shopping mall", "market"],
            "relaxation": ["spa", "beach"],
            "nightlife": ["bar", "club"]
        }
        
        categories = []
        for interest in interests:
            if interest in mapping:
                categories.extend(mapping[interest])
                
        return list(set(categories))  # Remove duplicates
    
    def _filter_by_budget(self, experiences, budget_level):
        """Fine-Tuning a Decoder Model
        To fine-tune a decoder model (like Qwen or LLaMA) to replace the Gemini API for narrative generation, you'll need:
        
        1. Training Data
        The existing saved itineraries in saved_itineraries/ are perfect examples. Each JSON file contains:
        
        User preferences (inputs)
        Generated narratives (outputs)
        2. Adapting the Narrative Service
        You'd need to modify the NarrativeService to:
        
        Load your fine-tuned model
        Format inputs similarly to how you'd train the model
        Generate outputs using your model instead of Gemini
        3. Model Design Considerations
        Your model would need to learn these key capabilities:
        
        Structure: Format content with days, activities, budget info
        Personalization: Adapt to interests, budget level, duration
        Knowledge: Incorporate destination-specific details (this might be harder)
        Filter or adjust experiences based on budget level.
        
        Parameters:
        -----------
        experiences : list
            List of experience dictionaries
        budget_level : str
            "low", "medium", or "high"
            
        Returns:
        --------
        list
            Filtered list of experiences
        """
        if budget_level == "low":
            # For low budget, exclude expensive experiences
            return [e for e in experiences if e["cost"] <= 30]
        elif budget_level == "medium":
            # For medium budget, include most experiences
            return experiences
        elif budget_level == "high":
            # For high budget, include premium experiences
            # In a real app, we might add more premium options here
            return experiences
        
        # Default to medium if invalid budget level
        return experiences