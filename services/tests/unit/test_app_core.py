import pytest
import sys
import os
from unittest.mock import patch, MagicMock
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import app_core
from app_core import generate_itinerary

class TestAppCore:
    
    def test_load_api_keys(self):
        # Test that the function attempts to load keys from environment or config
        keys = app_core.load_api_keys()
        assert isinstance(keys, dict)
        assert "FOURSQUARE_API_KEY" in keys
        assert "GEMINI_API_KEY" in keys
    
    @patch('app_core.get_popular_destinations')
    def test_get_popular_destinations(self, mock_get_destinations):
        # Mock the return value
        mock_get_destinations.return_value = [
            {"name": "Paris", "country": "France"},
            {"name": "Tokyo", "country": "Japan"}
        ]
        # Test that the function returns a list of destinations
        destinations = app_core.get_popular_destinations()
        assert isinstance(destinations, list)
    
    @patch('app_core.load_api_keys')
    @patch('app_core.LocationService')
    @patch('app_core.ExperienceService')
    @patch('app_core.BudgetService')
    @patch('app_core.NarrativeService')
    @patch('app_core.EvaluationService')
    @patch('app_core.ItineraryChatService')
    def test_generate_itinerary(self, mock_chat_service_class, mock_eval_service_class, 
                               mock_narrative_service_class, mock_budget_service_class, 
                               mock_experience_service_class, mock_location_service_class,
                               mock_load_api_keys):
        # Configure mocks
        mock_keys = {"FOURSQUARE_API_KEY": "test_key", "GEMINI_API_KEY": "test_key"}
        mock_load_api_keys.return_value = mock_keys
        
        # Set up mock service instances
        mock_location_instance = MagicMock()
        mock_experience_instance = MagicMock()
        mock_budget_instance = MagicMock()
        mock_narrative_instance = MagicMock()
        mock_eval_instance = MagicMock()
        mock_chat_instance = MagicMock()
        
        # Set up return values for class constructors
        mock_location_service_class.return_value = mock_location_instance
        mock_experience_service_class.return_value = mock_experience_instance
        mock_budget_service_class.return_value = mock_budget_instance
        mock_narrative_service_class.return_value = mock_narrative_instance
        mock_eval_service_class.return_value = mock_eval_instance
        mock_chat_service_class.return_value = mock_chat_instance
        
        # Configure methods on mock instances
        sample_experiences = [
            {"name": "Louvre Museum", "type": "museum", "cost": 15, "duration": 3}
        ]
        mock_experience_instance.suggest_experiences.return_value = sample_experiences
        
        sample_budget = {
            "accommodation": 300, "food": 150, "activities": 100, "transportation": 80, "total": 630
        }
        mock_budget_instance.calculate_budget.return_value = sample_budget
        
        sample_narrative = {
            "main_narrative": "Test narrative",
            "daily_plans": [{"day": 1, "content": "Day 1 plan"}],
            "budget_narrative": "Budget breakdown"
        }
        mock_narrative_instance.generate_narrative.return_value = sample_narrative
        
        mock_eval_instance.score.return_value = {
            "total": 85, "details": {"relevance": 90, "budget": 80}
        }
        
        # Configure the chat service's create_session method
        mock_chat_instance.create_session.return_value = "test_chat_id"
        
        # Sample preferences
        sample_preferences = {
            "destination": "Paris",
            "interests": ["art", "history", "food"],
            "budget_level": "medium",
            "trip_duration": 3
        }
        
        # Call the function
        result = generate_itinerary(sample_preferences)
        
        # Check that the result has the expected fields
        assert "narrative" in result
        assert "budget" in result
        assert "scores" in result
        assert "chat_id" in result
        
        # Check that the methods were called with the expected arguments
        mock_experience_instance.suggest_experiences.assert_called_once()
        mock_budget_instance.calculate_budget.assert_called_once()
        mock_narrative_instance.generate_narrative.assert_called_once()
        mock_eval_instance.score.assert_called_once()
        
        # Verify that create_session was called with the right arguments
        mock_chat_instance.create_session.assert_called_once_with(
            prefs=sample_preferences,
            narrative=sample_narrative,
            budget=sample_budget,
            experiences=sample_experiences,
            scores=mock_eval_instance.score.return_value
        )