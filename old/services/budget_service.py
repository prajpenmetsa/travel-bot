"""
Budget Service - Handles budget calculations based on destination, preferences, and trip duration.
"""

from typing import Dict, List, Any

class BudgetService:
    """Service for calculating budget estimates"""
    
    # Average costs per day by budget level and category
    BUDGET_TEMPLATES = {
        # Budget, Moderate, Luxury
        "accommodation": {
            "budget": {"min": 20, "max": 50},
            "moderate": {"min": 60, "max": 150},
            "luxury": {"min": 200, "max": 500}
        },
        "food": {
            "budget": {"min": 15, "max": 30},
            "moderate": {"min": 40, "max": 80},
            "luxury": {"min": 100, "max": 200}
        },
        "activities": {
            "budget": {"min": 0, "max": 20},
            "moderate": {"min": 30, "max": 80},
            "luxury": {"min": 100, "max": 300}
        },
        "transportation": {
            "budget": {"min": 5, "max": 15},
            "moderate": {"min": 20, "max": 50},
            "luxury": {"min": 80, "max": 200}
        }
    }
    
    # Region modifiers
    REGION_MODIFIERS = {
        # Southeast Asia, Eastern Europe, South America
        "budget_friendly": 0.7,
        # North America, Australia/NZ, Western Europe
        "expensive": 1.3,
        # Default
        "moderate": 1.0
    }
    
    # Mapping of countries/regions to cost categories
    REGION_COST_MAPPING = {
        # Budget-friendly regions
        "budget_friendly": [
            "thailand", "vietnam", "cambodia", "laos", "indonesia", "malaysia", 
            "philippines", "india", "bolivia", "colombia", "ecuador", "peru",
            "bulgaria", "romania", "hungary", "poland", "czech republic"
        ],
        # Expensive regions
        "expensive": [
            "united states", "canada", "australia", "new zealand", "japan", "singapore",
            "hong kong", "norway", "sweden", "denmark", "finland", "iceland",
            "switzerland", "france", "united kingdom", "ireland", "italy", "spain"
        ]
    }
    
    def __init__(self):
        """Initialize the budget service"""
        pass
    
    def calculate_budget(self, 
                       destination: str, 
                       interests: List[str], 
                       budget_level: str, 
                       trip_duration: int) -> Dict[str, Any]:
        """Calculate budget estimates for the trip"""
        
        # Determine region cost modifier
        region_modifier = self._get_region_modifier(destination)
        
        # Calculate costs for each category
        accommodation_cost = self._calculate_category_cost(
            "accommodation", budget_level, region_modifier
        )
        
        food_cost = self._calculate_category_cost(
            "food", budget_level, region_modifier
        )
        
        activities_cost = self._calculate_category_cost(
            "activities", budget_level, region_modifier
        )
        
        transportation_cost = self._calculate_category_cost(
            "transportation", budget_level, region_modifier
        )
        
        # Calculate daily and total costs
        daily_cost = accommodation_cost + food_cost + transportation_cost + activities_cost
        total_cost = daily_cost * trip_duration
        
        # Additional costs based on interests
        interest_adjustments = self._calculate_interest_adjustments(
            interests, budget_level, region_modifier, trip_duration
        )
        
        # Format budget breakdown
        budget_breakdown = {
            "per_day": {
                "accommodation": accommodation_cost,
                "food": food_cost,
                "transportation": transportation_cost,
                "activities": activities_cost,
                "total_daily": daily_cost
            },
            "total": {
                "accommodation": accommodation_cost * trip_duration,
                "food": food_cost * trip_duration,
                "transportation": transportation_cost * trip_duration,
                "activities": activities_cost * trip_duration,
                "adjustments": interest_adjustments,
                "grand_total": total_cost + interest_adjustments
            },
            "budget_level": budget_level,
            "region_type": self._get_region_type(destination)
        }
        
        return budget_breakdown
    
    def _get_region_modifier(self, destination: str) -> float:
        """Determine the cost modifier for a region"""
        destination_lower = destination.lower()
        
        # Check if destination is in budget-friendly regions
        for country in self.REGION_COST_MAPPING["budget_friendly"]:
            if country in destination_lower:
                return self.REGION_MODIFIERS["budget_friendly"]
        
        # Check if destination is in expensive regions
        for country in self.REGION_COST_MAPPING["expensive"]:
            if country in destination_lower:
                return self.REGION_MODIFIERS["expensive"]
        
        # Default to moderate
        return self.REGION_MODIFIERS["moderate"]
    
    def _get_region_type(self, destination: str) -> str:
        """Get the region type name for a destination"""
        destination_lower = destination.lower()
        
        # Check if destination is in budget-friendly regions
        for country in self.REGION_COST_MAPPING["budget_friendly"]:
            if country in destination_lower:
                return "budget_friendly"
        
        # Check if destination is in expensive regions
        for country in self.REGION_COST_MAPPING["expensive"]:
            if country in destination_lower:
                return "expensive"
        
        # Default to moderate
        return "moderate"
    
    def _calculate_category_cost(self, 
                              category: str, 
                              budget_level: str, 
                              region_modifier: float) -> float:
        """Calculate cost for a specific category"""
        # Get cost range for category and budget level
        cost_range = self.BUDGET_TEMPLATES[category][budget_level]
        
        # Calculate average cost and apply region modifier
        avg_cost = (cost_range["min"] + cost_range["max"]) / 2
        return round(avg_cost * region_modifier, 2)
    
    def _calculate_interest_adjustments(self, 
                                     interests: List[str], 
                                     budget_level: str, 
                                     region_modifier: float,
                                     trip_duration: int) -> float:
        """Calculate budget adjustments based on specific interests"""
        # Define interest cost factors
        interest_factors = {
            "food": 0.1,  # Food tours and experiences
            "adventure": 0.2,  # Adventure activities tend to be expensive
            "shopping": 0.15,  # Shopping budget
            "nightlife": 0.1,  # Nightlife budget
            "culture": 0.05,  # Museum entries, shows
        }
        
        # Base daily cost
        base_cost = sum([
            self._calculate_category_cost(category, budget_level, region_modifier)
            for category in ["accommodation", "food", "transportation", "activities"]
        ])
        
        # Calculate adjustments
        adjustment = 0
        for interest in interests:
            if interest in interest_factors:
                # Add percentage of base cost based on interest
                adjustment += base_cost * interest_factors[interest]
        
        # Apply to total trip
        return round(adjustment * trip_duration, 2)