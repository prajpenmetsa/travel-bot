import pytest
import sys
import os
import json
from pathlib import Path

# Add parent directory to path to make imports work
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import the services for testing
from preference_service import PreferenceService
from location_service import LocationService
from experience_service import ExperienceService
from budget_service import BudgetService
from narrative_service import NarrativeService
from evaluation_service import EvaluationService
from itinerary_chat_service import ItineraryChatService
from app_core import generate_itinerary

# Mock API keys for testing
@pytest.fixture
def mock_api_keys():
    return {
        "FOURSQUARE_API_KEY": "mock_foursquare_key",
        "GEMINI_API_KEY": "mock_gemini_key"
    }

# Service fixtures
@pytest.fixture
def preference_service():
    return PreferenceService()

@pytest.fixture
def location_service(mock_api_keys):
    return LocationService(api_key=mock_api_keys["FOURSQUARE_API_KEY"])

@pytest.fixture
def experience_service(location_service):
    return ExperienceService(location_service)

@pytest.fixture
def budget_service():
    return BudgetService()

@pytest.fixture
def narrative_service(mock_api_keys):
    return NarrativeService(api_key=mock_api_keys["GEMINI_API_KEY"])

@pytest.fixture
def evaluation_service():
    return EvaluationService()

@pytest.fixture
def itinerary_chat_service(mock_api_keys):
    return ItineraryChatService(api_key=mock_api_keys["GEMINI_API_KEY"])

# Sample test data
@pytest.fixture
def sample_preferences():
    return {
        "destination": "Paris",
        "interests": ["art", "history", "food"],
        "budget_level": "medium",
        "trip_duration": 3
    }

@pytest.fixture
def sample_experiences():
    return [
        {
            "name": "Louvre Museum",
            "type": "museum",
            "cost": 15,
            "duration": 3,
            "description": "World's largest art museum"
        },
        {
            "name": "Eiffel Tower",
            "type": "landmark",
            "cost": 25,
            "duration": 2,
            "description": "Iconic iron tower"
        },
        {
            "name": "Seine River Cruise",
            "type": "activity",
            "cost": 30,
            "duration": 1.5,
            "description": "Sightseeing boat tour"
        }
    ]

@pytest.fixture
def sample_budget():
    return {
        "accommodation": 300,
        "food": 180,
        "activities": 120,
        "transportation": 100,
        "total": 700
    }

@pytest.fixture
def sample_narrative():
    return {
        "main_narrative": "Experience the beauty of Paris with this 3-day itinerary.",
        "daily_plans": [
            {
                "day": 1,
                "content": "Start your day at the Louvre Museum, then enjoy lunch and explore Tuileries Garden."
            },
            {
                "day": 2,
                "content": "Visit the Eiffel Tower in the morning, followed by lunch at a local bistro."
            },
            {
                "day": 3,
                "content": "Take a Seine River Cruise and explore Montmartre."
            }
        ],
        "budget_narrative": "This medium-budget trip costs approximately €700 for 3 days."
    }

# Monkeypatch load_api_keys in app_core.py
@pytest.fixture
def patch_api_keys(monkeypatch, mock_api_keys):
    def mock_load_api_keys():
        return mock_api_keys
    
    monkeypatch.setattr('app_core.load_api_keys', mock_load_api_keys)

@pytest.fixture(scope='session')
def sample_fixture():
    return "sample data"