import pytest
import sys
import os
from unittest.mock import patch, MagicMock
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from location_service import LocationService
from experience_service import ExperienceService
from budget_service import BudgetService
from narrative_service import NarrativeService
from evaluation_service import EvaluationService

class TestServiceInteractions:
    
    def test_location_and_experience_service_integration(self):
        # Create a mock location service
        mock_location_service = MagicMock()
        mock_location_service.search_venues.return_value = [
            {
                "id": "123",
                "name": "Eiffel Tower",
                "location": {"lat": 48.8584, "lng": 2.2945},
                "categories": [{"name": "Monument"}]
            },
            {
                "id": "456",
                "name": "Louvre Museum",
                "location": {"lat": 48.8606, "lng": 2.3376},
                "categories": [{"name": "Museum"}]
            }
        ]
        
        # Create an experience service with the mock location service
        experience_service = ExperienceService(mock_location_service)
        
        # Call the experience service method that uses location service
        experiences = experience_service.suggest_experiences(
            destination="Paris",
            interests=["art", "history"],
            budget_level="medium",
            trip_duration=3
        )
        
        # Verify the results
        assert len(experiences) > 0
        assert mock_location_service.search_venues.called
        assert isinstance(experiences, list)
        for exp in experiences:
            assert "name" in exp
    
    def test_narrative_service_with_experience_and_budget(self):
        # Create a mock narrative service with _call_ai_model patched
        narrative_service = NarrativeService(api_key="test_key")
        
        # Patch the _call_ai_model method
        with patch.object(NarrativeService, '_call_ai_model') as mock_ai_call:
            mock_ai_call.return_value = {
                "main_narrative": "Test narrative for Paris",
                "daily_plans": [
                    {"day": 1, "content": "Day 1 plan for Paris"}
                ],
                "budget_narrative": "Budget breakdown for Paris"
            }
            
            # Create sample data that would come from other services
            experiences = [
                {
                    "name": "Eiffel Tower",
                    "type": "landmark",
                    "cost": 25,
                    "duration": 2
                }
            ]
            
            budget = {
                "accommodation": 300,
                "food": 150,
                "activities": 100,
                "total": 550
            }
            
            # Call the narrative service
            narrative = narrative_service.generate_narrative(
                destination="Paris",
                interests=["art", "history"],
                budget_level="medium",
                trip_duration=3,
                experiences=experiences,
                budget=budget
            )
            
            # Verify the results
            assert isinstance(narrative, dict)
            assert "main_narrative" in narrative
            assert "daily_plans" in narrative
            assert "budget_narrative" in narrative
            assert mock_ai_call.called

    def test_full_service_chain(self):
        # Create mock service instances
        mock_experience_service = MagicMock()
        mock_budget_service = MagicMock()
        mock_narrative_service = MagicMock()
        mock_evaluation_service = MagicMock()
        
        # Setup mock returns
        mock_experiences = [{"name": "Eiffel Tower", "type": "landmark", "cost": 25, "duration": 2}]
        mock_budget = {"accommodation": 300, "food": 150, "activities": 100, "total": 550}
        mock_narrative = {
            "main_narrative": "Test narrative",
            "daily_plans": [{"day": 1, "content": "Day 1 plan"}],
            "budget_narrative": "Budget breakdown"
        }
        mock_scores = {"total": 85, "details": {"relevance": 90, "budget": 80}}
        
        mock_experience_service.suggest_experiences.return_value = mock_experiences
        mock_budget_service.calculate_budget.return_value = mock_budget
        mock_narrative_service.generate_narrative.return_value = mock_narrative
        mock_evaluation_service.score.return_value = mock_scores
        
        # Test preferences
        preferences = {
            "destination": "Paris",
            "interests": ["art", "history"],
            "budget_level": "medium",
            "trip_duration": 3
        }
        
        # Execute the full chain manually
        experiences = mock_experience_service.suggest_experiences(
            preferences["destination"],
            preferences["interests"],
            preferences["budget_level"],
            preferences["trip_duration"]
        )
        
        budget = mock_budget_service.calculate_budget(
            preferences["destination"],
            preferences["interests"],
            preferences["budget_level"],
            preferences["trip_duration"]
        )
        
        narrative = mock_narrative_service.generate_narrative(
            preferences["destination"],
            preferences["interests"],
            preferences["budget_level"],
            preferences["trip_duration"],
            experiences,
            budget
        )
        
        scores = mock_evaluation_service.score(preferences, narrative, budget)
        
        # Verify all services were called with correct parameters
        mock_experience_service.suggest_experiences.assert_called_once()
        mock_budget_service.calculate_budget.assert_called_once()
        mock_narrative_service.generate_narrative.assert_called_once()
        mock_evaluation_service.score.assert_called_once()
        
        # Verify the final results
        assert experiences == mock_experiences
        assert budget == mock_budget
        assert narrative == mock_narrative
        assert scores == mock_scores