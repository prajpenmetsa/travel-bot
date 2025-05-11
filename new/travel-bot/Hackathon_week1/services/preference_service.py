"""
Preference Service - Handles user input validation and processing.
"""
from typing import List, Dict, Any
from pydantic import BaseModel


class TravelPreference(BaseModel):
    """Travel preference model for data validation"""
    destination: str
    interests: List[str]
    budget_level: str
    trip_duration: int


class PreferenceService:
    """Service for handling user preferences"""
    
    VALID_INTERESTS = [
        "history", "food", "adventure", "culture", 
        "nature", "relaxation", "shopping", "nightlife", "family"
    ]
    
    VALID_BUDGET_LEVELS = ["budget", "moderate", "luxury"]
    
    @staticmethod
    def validate_destination(destination: str) -> str:
        """Validate and normalize destination input"""
        if not destination or len(destination.strip()) < 2:
            raise ValueError("Destination must be at least 2 characters")
        return destination.strip().title()
    
    @staticmethod
    def validate_interests(interests: List[str]) -> List[str]:
        """Validate that interests are in the allowed list"""
        if not interests or len(interests) == 0:
            raise ValueError("At least one interest must be selected")
        
        # Convert to lowercase for comparison
        normalized_interests = [i.lower() for i in interests]
        
        # Check if all interests are valid
        invalid_interests = [i for i in normalized_interests 
                            if i not in PreferenceService.VALID_INTERESTS]
        
        if invalid_interests:
            raise ValueError(f"Invalid interests: {', '.join(invalid_interests)}")
        
        return normalized_interests
    
    @staticmethod
    def validate_budget_level(budget_level: str) -> str:
        """Validate that budget level is in the allowed list"""
        if budget_level.lower() not in PreferenceService.VALID_BUDGET_LEVELS:
            raise ValueError(f"Budget level must be one of: {', '.join(PreferenceService.VALID_BUDGET_LEVELS)}")
        return budget_level.lower()
    
    @staticmethod
    def validate_trip_duration(days: int) -> int:
        """Validate that trip duration is within acceptable range"""
        if not isinstance(days, int) or days < 1 or days > 14:
            raise ValueError("Trip duration must be between 1 and 14 days")
        return days
    
    @classmethod
    def process_preferences(cls, 
                          destination: str, 
                          interests: List[str], 
                          budget_level: str, 
                          trip_duration: int) -> Dict[str, Any]:
        """Process and validate all user preferences"""
        try:
            validated_data = {
                "destination": cls.validate_destination(destination),
                "interests": cls.validate_interests(interests),
                "budget_level": cls.validate_budget_level(budget_level),
                "trip_duration": cls.validate_trip_duration(trip_duration)
            }
            
            # Create and validate with Pydantic model
            preference_model = TravelPreference(**validated_data)
            
            return preference_model.model_dump()
            
        except ValueError as e:
            # Re-raise the validation error
            raise ValueError(f"Preference validation error: {str(e)}")