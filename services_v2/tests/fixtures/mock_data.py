{
    "mock_data": {
        "user": {
            "id": 1,
            "name": "John Doe",
            "preferences": {
                "budget": 1000,
                "location": "Paris"
            }
        },
        "itinerary": {
            "destination": "Paris",
            "activities": [
                {
                    "name": "Eiffel Tower",
                    "time": "10:00 AM"
                },
                {
                    "name": "Louvre Museum",
                    "time": "1:00 PM"
                }
            ]
        }
    },
    "DESTINATIONS": [
        {
            "name": "Paris",
            "country": "France",
            "description": "City of Lights",
            "popular_for": ["romance", "art", "food", "architecture"],
            "typical_costs": {
                "low": {"accommodation": 50, "food": 30, "activities": 20},
                "medium": {"accommodation": 100, "food": 60, "activities": 40},
                "high": {"accommodation": 200, "food": 100, "activities": 80}
            }
        },
        {
            "name": "Tokyo",
            "country": "Japan",
            "description": "Modern metropolis with traditional charm",
            "popular_for": ["technology", "food", "shopping", "culture"],
            "typical_costs": {
                "low": {"accommodation": 60, "food": 35, "activities": 25},
                "medium": {"accommodation": 120, "food": 70, "activities": 50},
                "high": {"accommodation": 250, "food": 120, "activities": 90}
            }
        }
    ],
    "LOCATIONS": [
        {
            "id": "abc123",
            "name": "Louvre Museum",
            "location": {"lat": 48.8606, "lng": 2.3376},
            "categories": ["museum", "art gallery", "tourist attraction"],
            "description": "World's largest art museum",
            "rating": 4.7,
            "price": "€€",
            "photos": ["url1", "url2"]
        },
        {
            "id": "def456",
            "name": "Eiffel Tower",
            "location": {"lat": 48.8584, "lng": 2.2945},
            "categories": ["landmark", "tourist attraction"],
            "description": "Iconic iron tower",
            "rating": 4.8,
            "price": "€€",
            "photos": ["url3", "url4"]
        }
    ],
    "EXPERIENCES": [
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
        }
    ],
    "SAMPLE_BUDGET": {
        "accommodation": 300,
        "food": 180,
        "activities": 120,
        "transportation": 100,
        "total": 700
    },
    "SAMPLE_NARRATIVE": {
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
}