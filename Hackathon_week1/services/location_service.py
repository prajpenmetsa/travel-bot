"""
Location Service - Handles retrieval of location data from OpenTripMap API.
"""

import os
import json
import requests
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class LocationService:
    """Service for retrieving location data"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key and data cache"""
        self.api_key = api_key or os.environ.get("OPENTRIPMAP_API_KEY")
        if not self.api_key:
            logger.warning("OpenTripMap API key not found. Some features may be limited.")
        
        self.base_url = "https://api.opentripmap.com/0.1/en/places"
        self.cache = {}
        self.try_load_cache()
    
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
            url = f"{self.base_url}/geoname"
            params = {
                "name": location,
                "apikey": self.api_key,
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Cache the result
            self.cache[cache_key] = data
            self.save_cache()
            
            return data
        except Exception as e:
            logger.error(f"Error fetching geoname for {location}: {e}")
            return self._get_fallback_geoname(location)
    
    def _get_fallback_geoname(self, location: str) -> Dict[str, Any]:
        """Fallback when API is unavailable"""
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
            
            # Convert interests to OpenTripMap categories
            kinds = self._map_interests_to_kinds(interests)
            
            # Get radius based on whether it's a city or country
            radius = 5000  # Default for city (5km)
            
            # Get points of interest
            url = f"{self.base_url}/radius"
            params = {
                "radius": radius,
                "lon": lon,
                "lat": lat,
                "kinds": kinds,
                "rate": "3h",  # Include highly-rated places
                "limit": limit,
                "apikey": self.api_key,
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Cache the result
            processed_data = [
                {
                    "name": item.get("name", "Unknown place"),
                    "kinds": item.get("kinds", "").split(","),
                    "distance": item.get("dist", 0),
                    "xid": item.get("xid", "")
                }
                for item in data.get("features", [])
            ]
            
            # Get details for top points of interest
            for i, poi in enumerate(processed_data[:min(5, len(processed_data))]):
                if poi.get("xid"):
                    details = self._get_poi_details(poi["xid"])
                    processed_data[i].update(details)
            
            self.cache[cache_key] = processed_data
            self.save_cache()
            
            return processed_data
        except Exception as e:
            logger.error(f"Error fetching POIs for {location} with interests {interests}: {e}")
            return self._get_fallback_poi(location, interests)
    
    def _get_poi_details(self, xid: str) -> Dict[str, Any]:
        """Get details for a specific point of interest"""
        cache_key = f"poi_details:{xid}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            url = f"{self.base_url}/xid/{xid}"
            params = {"apikey": self.api_key}
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            details = {
                "description": data.get("wikipedia_extracts", {}).get("text", ""),
                "image": data.get("preview", {}).get("source", ""),
                "address": data.get("address", {}).get("formatted", ""),
                "website": data.get("url", "")
            }
            
            self.cache[cache_key] = details
            return details
        except Exception as e:
            logger.error(f"Error fetching POI details for {xid}: {e}")
            return {}
    
    def _map_interests_to_kinds(self, interests: List[str]) -> str:
        """Map user interests to OpenTripMap kinds"""
        interest_to_kinds = {
            "history": "historic,museums,architecture,religion,archaeology",
            "food": "foods,breweries,wineries,restaurants,cafes",
            "adventure": "sport,amusements,natural",
            "culture": "cultural,museums,theatres_and_entertainments,religion",
            "nature": "natural,parks,beaches,gardens",
            "relaxation": "beaches,gardens,spas,parks",
            "shopping": "commercial,shops,malls",
            "nightlife": "bars,foods,theatres_and_entertainments,casinos",
            "family": "amusements,zoos,parks,museums"
        }
        
        # Combine all relevant kinds
        kinds_set = set()
        for interest in interests:
            if interest in interest_to_kinds:
                kinds_set.update(interest_to_kinds[interest].split(","))
        
        return ",".join(kinds_set) if kinds_set else "interesting_places"
    
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