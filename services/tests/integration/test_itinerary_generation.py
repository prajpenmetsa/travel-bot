import pytest
import sys
import os
from unittest.mock import patch, MagicMock
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import app_core
from location_service import LocationService
from experience_service import ExperienceService

class TestItineraryGeneration:
    
    @patch('app_core.load_api_keys')
    def test_end_to_end_itinerary_generation(self, mock_load_api_keys):
        # Configure mock APIs
        mock_load_api_keys.return_value = {
            "FOURSQUARE_API_KEY": "test_key",
            "GEMINI_API_KEY": "test_key"
        }
        
        # Set up mock service classes
        with patch('app_core.LocationService') as mock_loc_service_class, \
             patch('app_core.ExperienceService') as mock_exp_service_class, \
             patch('app_core.BudgetService') as mock_bud_service_class, \
             patch('app_core.NarrativeService') as mock_nar_service_class, \
             patch('app_core.EvaluationService') as mock_eval_service_class, \
             patch('app_core.ItineraryChatService') as mock_chat_service_class:
             
            # Set up mock service instances
            mock_loc_service = MagicMock()
            mock_exp_service = MagicMock()
            mock_bud_service = MagicMock()
            mock_nar_service = MagicMock()
            mock_eval_service = MagicMock()
            mock_chat_service = MagicMock()
            
            # Set up return values for class constructors
            mock_loc_service_class.return_value = mock_loc_service
            mock_exp_service_class.return_value = mock_exp_service
            mock_bud_service_class.return_value = mock_bud_service
            mock_nar_service_class.return_value = mock_nar_service
            mock_eval_service_class.return_value = mock_eval_service
            mock_chat_service_class.return_value = mock_chat_service
            
            # Set up return values for methods
            mock_exp_service.suggest_experiences.return_value = [
                {"name": "Louvre Museum", "type": "museum", "cost": 15, "duration": 3}
            ]
            
            mock_bud_service.calculate_budget.return_value = {
                "accommodation": 300, "food": 150, "activities": 100, "total": 550
            }
            
            mock_nar_service.generate_narrative.return_value = {
                "main_narrative": "Test narrative",
                "daily_plans": [{"day": 1, "content": "Day 1 plan"}],
                "budget_narrative": "Budget breakdown"
            }
            
            mock_eval_service.score.return_value = {
                "total": 85, "details": {"relevance": 90, "budget": 80}
            }
            
            # Configure the create_session method correctly
            mock_chat_service.create_session.return_value = "test_chat_id"
            
            # Sample preferences
            sample_preferences = {
                "destination": "Paris",
                "interests": ["art", "history", "food"],
                "budget_level": "medium",
                "trip_duration": 3
            }
            
            # Call generate_itinerary
            result = app_core.generate_itinerary(sample_preferences)
            
            # Verify the result structure
            assert "narrative" in result
            assert "budget" in result
            assert "scores" in result
            assert "chat_id" in result
            assert result["chat_id"] == "test_chat_id"
            
            # Verify create_session was called with the expected arguments
            mock_chat_service.create_session.assert_called_once()
    
    @patch('app_core.load_api_keys')
    def test_integration_with_real_services(self, mock_load_api_keys):
        # Mock the API keys
        mock_load_api_keys.return_value = {
            "FOURSQUARE_API_KEY": "test_key", 
            "GEMINI_API_KEY": "test_key"
        }
        
        # Create a real LocationService instance
        loc_service = LocationService(api_key="test_key")
        
        # Patch the LocationService.search_venues method
        with patch.object(LocationService, 'search_venues') as mock_search_venues:
            # Mock the external API call in LocationService
            mock_search_venues.return_value = [
                {
                    "id": "abc123",
                    "name": "Eiffel Tower",
                    "location": {"lat": 48.8584, "lng": 2.2945},
                    "categories": [{"name": "Monument"}]
                }
            ]
            
            # Create a real ExperienceService with our mocked LocationService
            exp_service = ExperienceService(loc_service)
            
            # Now patch the app_core imports to use our instances
            with patch('app_core.LocationService', return_value=loc_service), \
                 patch('app_core.ExperienceService', return_value=exp_service), \
                 patch('app_core.BudgetService') as mock_bud_class, \
                 patch('app_core.NarrativeService') as mock_nar_class, \
                 patch('app_core.EvaluationService') as mock_eval_class, \
                 patch('app_core.ItineraryChatService') as mock_chat_class:
                
                # Set up mock instances for the remaining services
                mock_bud_service = MagicMock()
                mock_nar_service = MagicMock()
                mock_eval_service = MagicMock()
                mock_chat_service = MagicMock()
                
                mock_bud_class.return_value = mock_bud_service
                mock_nar_class.return_value = mock_nar_service
                mock_eval_class.return_value = mock_eval_service
                mock_chat_class.return_value = mock_chat_service
                
                # Configure return values
                mock_bud_service.calculate_budget.return_value = {
                    "accommodation": 300, "food": 150, "activities": 100, "total": 550
                }
                
                mock_nar_service.generate_narrative.return_value = {
                    "main_narrative": "Test narrative",
                    "daily_plans": [{"day": 1, "content": "Day 1 plan"}],
                    "budget_narrative": "Budget breakdown"
                }
                
                mock_eval_service.score.return_value = {
                    "total": 85, "details": {"relevance": 90, "budget": 80}
                }
                
                # Configure create_session correctly
                mock_chat_service.create_session.return_value = "test_chat_id"
                
                # Sample preferences
                sample_preferences = {
                    "destination": "Paris",
                    "interests": ["art", "history", "food"],
                    "budget_level": "medium",
                    "trip_duration": 3
                }
                
                # Call generate_itinerary
                result = app_core.generate_itinerary(sample_preferences)
                
                # Check the result
                assert "narrative" in result
                assert "budget" in result
                assert "scores" in result
                assert isinstance(result["budget"], dict)
                assert "total" in result["budget"]