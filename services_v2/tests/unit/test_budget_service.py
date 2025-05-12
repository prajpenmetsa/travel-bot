import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from budget_service import BudgetService

class TestBudgetService:
    def test_calculate_budget(self, budget_service):
        # Test calculating budget for a destination
        budget = budget_service.calculate_budget(
            destination="Paris",
            interests=["art", "history", "food"],
            budget_level="medium",
            trip_duration=3
        )
        
        # Assert budget has all required components
        assert isinstance(budget, dict)
        assert "accommodation" in budget
        assert "food" in budget
        assert "activities" in budget
        assert "total" in budget
        
        # Total should be sum of components
        components_sum = sum(v for k, v in budget.items() if k != "total")
        assert budget["total"] == components_sum
    
    def test_budget_level_scaling(self, budget_service):
        # Test that different budget levels return different totals
        low_budget = budget_service.calculate_budget(
            destination="Paris",
            interests=["art"],
            budget_level="low",
            trip_duration=3
        )
        
        medium_budget = budget_service.calculate_budget(
            destination="Paris",
            interests=["art"],
            budget_level="medium",
            trip_duration=3
        )
        
        high_budget = budget_service.calculate_budget(
            destination="Paris",
            interests=["art"],
            budget_level="high",
            trip_duration=3
        )
        
        # Higher budget levels should cost more
        assert low_budget["total"] < medium_budget["total"]
        assert medium_budget["total"] < high_budget["total"]
    
    def test_trip_duration_scaling(self, budget_service):
        # Test that longer trips cost more
        short_trip = budget_service.calculate_budget(
            destination="Paris",
            interests=["art"],
            budget_level="medium",
            trip_duration=3
        )
        
        long_trip = budget_service.calculate_budget(
            destination="Paris",
            interests=["art"],
            budget_level="medium",
            trip_duration=7
        )
        
        # Longer trip should cost more
        assert long_trip["total"] > short_trip["total"]
        # Longer trip should be approximately proportional to duration
        ratio = long_trip["total"] / short_trip["total"]
        expected_ratio = 7 / 3
        assert abs(ratio - expected_ratio) < 0.5  # Allow some wiggle room in the ratio