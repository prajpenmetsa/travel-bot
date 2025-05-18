"""
Budget calculation service for travel itineraries.
"""

from typing import Dict, List, Any

class BudgetService:
    """Service for calculating travel budgets based on destination and preferences."""
    
    def __init__(self):
        # Initialize with base costs for different budget levels
        self.base_costs = {
            "low": {
                "accommodation": 50,
                "food": 30, 
                "activities": 20,
                "transportation": 15
            },
            "medium": {
                "accommodation": 100,
                "food": 60,
                "activities": 40,
                "transportation": 30
            },
            "high": {
                "accommodation": 200,
                "food": 100,
                "activities": 80,
                "transportation": 60
            }
        }
        
        # City cost multipliers (relative to base costs)
        self.city_multipliers = {
            "Paris": 1.2,
            "Tokyo": 1.3,
            "New York": 1.5,
            "London": 1.4,
            "Bangkok": 0.7,
            "Rome": 1.1,
            "Sydney": 1.3,
            # Default for cities not explicitly listed
            "default": 1.0
        }
        
        # Interest cost multipliers
        self.interest_multipliers = {
            "food": 1.2,  # Food tours and dining experiences cost more
            "luxury": 1.5,  # Luxury experiences cost more
            "adventure": 1.3,  # Adventure activities cost more
            # Default for interests not explicitly listed
            "default": 1.0
        }
    
    def calculate_budget(self, destination, interests, budget_level, trip_duration):
        """
        Calculate a detailed budget for the trip based on preferences.
        
        Parameters:
        -----------
        destination : str
            The city or location name
        interests : list
            List of interest categories (e.g., ["food", "history", "art"])
        budget_level : str
            "low", "medium", or "high"
        trip_duration : int
            Number of days for the trip
        
        Returns:
        --------
        dict
            Budget breakdown with categories and total
        """
        if budget_level not in self.base_costs:
            budget_level = "medium"  # Default to medium if invalid level provided
            
        # Get base costs for the specified budget level
        base = self.base_costs[budget_level]
        
        # Get city cost multiplier
        city_multiplier = self.city_multipliers.get(destination, self.city_multipliers["default"])
        
        # Calculate interest multiplier based on the average of relevant interests
        interest_mults = [self.interest_multipliers.get(i, self.interest_multipliers["default"]) 
                          for i in interests]
        interest_multiplier = sum(interest_mults) / max(1, len(interest_mults))
        
        # Calculate budget components, adjusting for all factors and trip duration
        budget = {
            "accommodation": round(base["accommodation"] * city_multiplier * trip_duration),
            "food": round(base["food"] * city_multiplier * interest_multiplier * trip_duration),
            "activities": round(base["activities"] * city_multiplier * interest_multiplier * trip_duration),
            "transportation": round(base["transportation"] * city_multiplier * trip_duration)
        }
        
        # Add total
        budget["total"] = sum(budget.values())
        
        return budget