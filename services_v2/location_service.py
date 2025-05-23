"""
Location Service - Handles retrieval of location data from Foursquare API.
"""

import os
import json
import requests
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class LocationService:
    """Service for retrieving location data and venue information."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key and data cache"""
        self.api_key = api_key or os.environ.get("FOURSQUARE_API_KEY")
        if not self.api_key:
            logger.warning("Foursquare API key not found. Some features may be limited.")
        
        self.base_url = "https://api.foursquare.com/v3"
        self.cache = {}
        self.try_load_cache()
        self._destinations_cache = None
    
    def try_load_cache(self) -> None:
        """Load cache from file if it exists"""
        cache_file = Path("data/location_cache.json")
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    self.cache = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
    
    def save_cache(self) -> None:
        """Save cache to file"""
        cache_file = Path("data/location_cache.json")
        cache_file.parent.mkdir(exist_ok=True)
        try:
            with open(cache_file, "w") as f:
                json.dump(self.cache, f)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def get_geoname(self, location: str) -> Dict[str, Any]:
        """Get geoname information for a location"""
        cache_key = f"geoname:{location.lower()}"
        
        # Check cache first
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Get from API if API key is available
        if not self.api_key:
            return self._get_fallback_geoname(location)
        
        try:
            # Using Foursquare geocoding endpoint
            url = f"{self.base_url}/places/geocode"
            headers = {
                "Accept": "application/json",
                "Authorization": self.api_key
            }
            params = {
                "query": location,
                "limit": 1
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extract location data
            if data and "results" in data and len(data["results"]) > 0:
                result = data["results"][0]
                geo_data = {
                    "name": location,
                    "country": result.get("address", {}).get("country", "Unknown"),
                    "lat": result.get("geocodes", {}).get("main", {}).get("latitude", 0),
                    "lon": result.get("geocodes", {}).get("main", {}).get("longitude", 0),
                }
                
                # Cache the result
                self.cache[cache_key] = geo_data
                self.save_cache()
                
                return geo_data
            else:
                return self._get_fallback_geoname(location)
                
        except Exception as e:
            logger.error(f"Error fetching geoname for {location}: {e}")
            return self._get_fallback_geoname(location)
    
    def _get_fallback_geoname(self, location: str) -> Dict[str, Any]:
        """Fallback when API is unavailable"""
        # Some common city coordinates
        location_data = {
            "delhi": {"lat": 28.7041, "lon": 77.1025, "country": "India"},
            "new york": {"lat": 40.7128, "lon": -74.0060, "country": "United States"},
            "london": {"lat": 51.5072, "lon": -0.1276, "country": "United Kingdom"},
            "paris": {"lat": 48.8566, "lon": 2.3522, "country": "France"},
            "tokyo": {"lat": 35.6762, "lon": 139.6503, "country": "Japan"},
            # Add more cities as needed
        }
        
        loc_lower = location.lower()
        if loc_lower in location_data:
            data = location_data[loc_lower]
            return {
                "name": location,
                "country": data["country"],
                "lat": data["lat"],
                "lon": data["lon"],
            }
        else:
            return {
                "name": location,
                "country": "Unknown",
                "lat": 0,
                "lon": 0,
            }
    
    def get_points_of_interest(self, location: str, interests: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Get points of interest for a location based on user interests"""
        cache_key = f"poi:{location.lower()}:{'-'.join(sorted(interests))}"
        
        # Check cache first
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # If no API key, return fallback data
        if not self.api_key:
            return self._get_fallback_poi(location, interests)
        
        try:
            # First, get geocoordinates
            geoname = self.get_geoname(location)
            lat, lon = geoname.get("lat", 0), geoname.get("lon", 0)
            
            if lat == 0 and lon == 0:
                logger.warning(f"Could not find coordinates for {location}, using fallback POIs")
                return self._get_fallback_poi(location, interests)
            
            # Convert interests to Foursquare categories
            categories = self._map_interests_to_categories(interests)
            
            # Get points of interest
            url = f"{self.base_url}/places/search"
            headers = {
                "Accept": "application/json",
                "Authorization": self.api_key
            }
            params = {
                "ll": f"{lat},{lon}",
                "radius": 5000,
                "categories": categories,
                "sort": "POPULARITY",
                "limit": limit
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Process the Foursquare response
            processed_data = []
            for item in data.get("results", []):
                poi_data = {
                    "name": item.get("name", "Unknown place"),
                    "kinds": [cat.get("name", "unknown") for cat in item.get("categories", [])],
                    "distance": item.get("distance", 0),
                    "xid": item.get("fsq_id", ""),
                    "description": item.get("description", ""),
                    "address": ", ".join(item.get("location", {}).get("formatted_address", [])),
                    "website": item.get("website", ""),
                    "image": next((photo.get("prefix", "") + "original" + photo.get("suffix", "") 
                                  for photo in item.get("photos", [])), "")
                }
                processed_data.append(poi_data)
            
            # Cache the result
            self.cache[cache_key] = processed_data
            self.save_cache()
            
            return processed_data
        except Exception as e:
            logger.error(f"Error fetching POIs for {location} with interests {interests}: {e}")
            return self._get_fallback_poi(location, interests)
    
    def _map_interests_to_categories(self, interests: List[str]) -> str:
        """Map user interests to Foursquare category IDs"""
        # Foursquare category IDs
        interest_to_categories = {
            "history": "16000,16007,16008", # landmarks, historic sites, monuments
            "food": "13000,13065,13263", # food, restaurants, cafes
            "adventure": "19000,19013,19014", # outdoors, trails, parks
            "culture": "10000,10017,10018", # arts & entertainment, museums, theaters
            "nature": "19000,19013,19014,19043", # outdoors, trails, parks, beaches
            "relaxation": "14000,14001,14114", # professional services, spas, wellness
            "shopping": "17000,17020,17090", # shops, malls, boutiques
            "nightlife": "10032,10035,11000", # nightlife, bars, clubs
            "family": "12000,12054,19012,10000" # attractions for kids, playgrounds, zoos, entertainment
        }
        
        # Combine all relevant categories
        categories_list = []
        for interest in interests:
            if interest in interest_to_categories:
                categories_list.append(interest_to_categories[interest])
        
        return ",".join(categories_list) if categories_list else "10000,13000,17000" # default categories
    
    def _get_fallback_poi(self, location: str, interests: List[str]) -> List[Dict[str, Any]]:
        """Fallback POI data when API is unavailable"""
        # Generic POIs by category
        generic_pois = {
            "history": [
                {"name": f"{location} History Museum", "kinds": ["museums", "historic"]},
                {"name": f"Old Town {location}", "kinds": ["historic", "architecture"]},
                {"name": f"{location} Heritage Site", "kinds": ["historic"]}
            ],
            "food": [
                {"name": f"{location} Food Market", "kinds": ["foods"]},
                {"name": f"Traditional {location} Restaurant", "kinds": ["restaurants"]},
                {"name": f"{location} Culinary Tour", "kinds": ["foods"]}
            ],
            "adventure": [
                {"name": f"{location} Adventure Park", "kinds": ["sport", "amusements"]},
                {"name": f"{location} Hiking Trail", "kinds": ["natural", "sport"]},
                {"name": f"{location} Outdoor Activities", "kinds": ["sport"]}
            ],
            "culture": [
                {"name": f"{location} Art Gallery", "kinds": ["cultural", "museums"]},
                {"name": f"{location} Cultural Center", "kinds": ["cultural"]},
                {"name": f"{location} Theatre", "kinds": ["theatres_and_entertainments"]}
            ],
            "nature": [
                {"name": f"{location} National Park", "kinds": ["natural", "parks"]},
                {"name": f"{location} Botanical Garden", "kinds": ["gardens"]},
                {"name": f"{location} Scenic Viewpoint", "kinds": ["natural"]}
            ],
            "relaxation": [
                {"name": f"{location} Spa Resort", "kinds": ["spas"]},
                {"name": f"{location} Beach", "kinds": ["beaches"]},
                {"name": f"{location} Wellness Center", "kinds": ["spas"]}
            ],
            "shopping": [
                {"name": f"{location} Shopping District", "kinds": ["commercial", "shops"]},
                {"name": f"{location} Local Market", "kinds": ["shops"]},
                {"name": f"{location} Artisan Shops", "kinds": ["shops"]}
            ],
            "nightlife": [
                {"name": f"{location} Nightclub", "kinds": ["bars"]},
                {"name": f"{location} Evening Entertainment", "kinds": ["theatres_and_entertainments"]},
                {"name": f"{location} Night Market", "kinds": ["foods"]}
            ],
            "family": [
                {"name": f"{location} Family Park", "kinds": ["parks", "amusements"]},
                {"name": f"{location} Zoo", "kinds": ["zoos"]},
                {"name": f"{location} Family-friendly Museum", "kinds": ["museums"]}
            ]
        }
        
        # Combine POIs based on user interests
        pois = []
        for interest in interests:
            if interest in generic_pois:
                pois.extend(generic_pois[interest])
        
        # Add descriptions
        for poi in pois:
            poi["description"] = f"A popular {'/'.join(poi['kinds'])} destination in {location}."
        
        return pois[:10]  # Limit to 10 POIs
    
    def get_popular_destinations(self):
        """
        Get a list of popular travel destinations.
        
        Returns:
        --------
        list
            List of destination dictionaries with name, country, etc.
        """
        if self._destinations_cache is None:
            try:
                # Try to load from local file first
                root = Path(__file__).resolve().parent
                candidates = [
                    root / "data" / "destinations.json",
                    root.parent / "data" / "destinations.json",
                ]
                
                for p in candidates:
                    if p.exists():
                        with p.open() as f:
                            data = json.load(f)
                            self._destinations_cache = data.get("popular_destinations", [])
                            break
                
                # If no file found, use default list
                if self._destinations_cache is None:
                    self._destinations_cache = [
                        {"name": "Paris", "country": "France", "continent": "Europe"},
                        {"name": "Tokyo", "country": "Japan", "continent": "Asia"},
                        {"name": "New York", "country": "USA", "continent": "North America"},
                        {"name": "London", "country": "UK", "continent": "Europe"},
                        {"name": "Rome", "country": "Italy", "continent": "Europe"},
                    ]
            except Exception as e:
                print(f"Error loading destinations: {e}")
                self._destinations_cache = []
                
        return self._destinations_cache
    
    def search_venues(self, destination, categories=None, limit=10):
        """
        Search for venues in a destination based on categories.
        
        Parameters:
        -----------
        destination : str
            City or location name
        categories : list, optional
            List of venue categories to filter by
        limit : int, optional
            Maximum number of results to return
            
        Returns:
        --------
        list
            List of venue dictionaries with details
        """
        # If we have an API key, try to use the external API
        if self.api_key:
            try:
                return self._search_venues_api(destination, categories, limit)
            except Exception as e:
                print(f"API search failed: {e}, falling back to mock data")
        
        # Otherwise use mock data
        return self._get_mock_venues(destination, categories, limit)
    
    def _search_venues_api(self, destination, categories=None, limit=10):
        """
        Search for venues using the Foursquare Places API.
        
        Parameters:
        -----------
        destination : str
            City or location name
        categories : list, optional
            List of venue categories to filter by
        limit : int, optional
            Maximum number of results to return
            
        Returns:
        --------
        list
            List of venue dictionaries with details
        """
        # Mock implementation - in a real app, this would call the Foursquare API
        url = "https://api.foursquare.com/v3/places/search"
        
        params = {
            "near": destination,
            "limit": limit,
        }
        
        if categories:
            params["categories"] = ",".join(categories)
        
        headers = {
            "Accept": "application/json",
            "Authorization": self.api_key
        }
        
        # In real implementation, we would uncomment this:
        # response = requests.get(url, headers=headers, params=params)
        # return response.json()["results"]
        
        # For testing, return mock data
        return self._get_mock_venues(destination, categories, limit)
    
    def _get_mock_venues(self, destination, categories=None, limit=10):
        """
        Get mock venue data for testing when API is not available.
        
        Parameters are same as search_venues.
        """
        mock_venues = {
            "Paris": [
                {
                    "id": "abc123",
                    "name": "Louvre Museum",
                    "location": {"lat": 48.8606, "lng": 2.3376},
                    "categories": [{"name": "Museum"}, {"name": "Art Gallery"}]
                },
                {
                    "id": "def456",
                    "name": "Eiffel Tower",
                    "location": {"lat": 48.8584, "lng": 2.2945},
                    "categories": [{"name": "Monument"}, {"name": "Landmark"}]
                },
                {
                    "id": "ghi789",
                    "name": "Notre-Dame Cathedral",
                    "location": {"lat": 48.8530, "lng": 2.3499},
                    "categories": [{"name": "Historic Site"}, {"name": "Church"}]
                }
            ],
            "Tokyo": [
                {
                    "id": "jkl012",
                    "name": "Tokyo Skytree",
                    "location": {"lat": 35.7100, "lng": 139.8107},
                    "categories": [{"name": "Tower"}, {"name": "Observation Deck"}]
                },
                {
                    "id": "mno345",
                    "name": "Senso-ji Temple",
                    "location": {"lat": 35.7147, "lng": 139.7966},
                    "categories": [{"name": "Temple"}, {"name": "Historic Site"}]
                }
            ]
        }
        
        # Return venues for the specified destination, or empty list if not found
        venues = mock_venues.get(destination, [])
        
        # Filter by categories if specified
        if categories:
            filtered = []
            for venue in venues:
                venue_categories = [cat["name"].lower() for cat in venue["categories"]]
                for category in categories:
                    if category.lower() in venue_categories:
                        filtered.append(venue)
                        break
            venues = filtered
        
        return venues[:limit]