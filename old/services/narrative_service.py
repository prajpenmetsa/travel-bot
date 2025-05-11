"""
Narrative Service - Handles generating compelling travel narratives using Gemini AI.
"""

import os
import logging
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from utils.prompts import (
    NARRATIVE_PROMPT_TEMPLATE,
    DAY_PLAN_PROMPT_TEMPLATE,
    BUDGET_PROMPT_TEMPLATE
)

logger = logging.getLogger(__name__)

class NarrativeService:
    """Service for generating compelling travel narratives"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the narrative service with the Gemini API"""
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
        else:
            logger.warning("Gemini API key not found. Using fallback narrative generation.")
    
    def generate_narrative(self, 
                         destination: str, 
                         interests: List[str], 
                         budget_level: str, 
                         trip_duration: int,
                         experiences: Dict[str, Any],
                         budget: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a compelling travel narrative using Gemini AI"""
        
        # Extract points of interest
        points_of_interest = experiences.get("points_of_interest", [])
        poi_names = [poi.get("name", "Unnamed place") for poi in points_of_interest[:5]]
        
        if not self.api_key:
            return self._generate_fallback_narrative(
                destination, interests, budget_level, trip_duration, experiences, budget
            )
        
        try:
            # Format interests for prompt
            interests_str = ", ".join(interests)
            
            # Format points of interest for prompt
            poi_str = ", ".join(poi_names)
            
            # Create a prompt from template
            prompt = NARRATIVE_PROMPT_TEMPLATE.format(
                destination=destination,
                interests=interests_str,
                budget_level=budget_level,
                days=trip_duration,
                points_of_interest=poi_str
            )
            
            # Generate narrative with Gemini
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content(prompt)
            narrative = response.text
            
            # Generate detailed day plans
            daily_plans = []
            for day_num in range(1, trip_duration + 1):
                day_prompt = DAY_PLAN_PROMPT_TEMPLATE.format(
                    day_number=day_num,
                    days_total=trip_duration,
                    destination=destination,
                    interests=interests_str,
                    budget_level=budget_level
                )
                day_response = model.generate_content(day_prompt)
                daily_plans.append({
                    "day": day_num,
                    "content": day_response.text
                })
            
            # Generate budget narrative
            budget_prompt = BUDGET_PROMPT_TEMPLATE.format(
                days=trip_duration,
                destination=destination,
                budget_level=budget_level,
                interests=interests_str
            )
            budget_response = model.generate_content(budget_prompt)
            budget_narrative = budget_response.text
            
            return {
                "main_narrative": narrative,
                "daily_plans": daily_plans,
                "budget_narrative": budget_narrative
            }
        
        except Exception as e:
            logger.error(f"Error generating narrative with Gemini: {e}")
            return self._generate_fallback_narrative(
                destination, interests, budget_level, trip_duration, experiences, budget
            )
    
    def _generate_fallback_narrative(self, 
                                   destination: str, 
                                   interests: List[str], 
                                   budget_level: str, 
                                   trip_duration: int,
                                   experiences: Dict[str, Any],
                                   budget: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a fallback narrative when Gemini API is unavailable"""
        
        interests_str = ", ".join(interests)
        
        # Create main narrative
        main_narrative = f"""
# Your {trip_duration}-Day {budget_level.title()} Adventure in {destination}

Imagine yourself arriving in the vibrant destination of {destination}, where {trip_duration} days of {interests_str} experiences await you. This personalized journey combines the best of what {destination} has to offer for travelers who love {interests_str}.

## Trip Highlights

{destination} offers the perfect blend of experiences for your interests. Each day will bring new discoveries and memories to cherish.

## What Makes This Trip Special

This itinerary is specially crafted to match your interest in {interests_str} while keeping to a {budget_level} budget. You'll get to experience authentic local culture, savor delicious cuisine, and create unforgettable memories.

## Budget Overview

* Accommodations: ${budget["per_day"]["accommodation"]} per night
* Food: ${budget["per_day"]["food"]} per day
* Activities: ${budget["per_day"]["activities"]} per day
* Transportation: ${budget["per_day"]["transportation"]} per day
* Total Estimated Cost: ${budget["total"]["grand_total"]} for the entire trip

Are you ready to discover the magic of {destination}? Let's dive into your day-by-day adventure!
"""
        
        # Create daily plans
        daily_plans = []
        for day_num in range(1, trip_duration + 1):
            # Get activities for this day
            day_activities = []
            for plan in experiences.get("daily_plans", []):
                if plan.get("day") == day_num:
                    day_activities = plan.get("activities", [])
                    break
            
            activity_names = [act.get("name", "Explore the area") for act in day_activities]
            if not activity_names:
                activity_names = [f"Explore {destination}", f"Experience local {interests[0]} scene"]
            
            daily_content = f"""
# Day {day_num} - {destination} Adventure

## Morning
* Start your day with a visit to {activity_names[0] if activity_names else f'a local spot in {destination}'}
* Enjoy breakfast at a local café

## Afternoon
* {activity_names[1] if len(activity_names) > 1 else f'Discover more of {destination}'}
* Have lunch at a {budget_level} restaurant featuring local cuisine

## Evening
* Relax and enjoy the {destination} atmosphere
* Dinner at a {budget_level} spot known for its {interests[0] if interests else 'local'} offerings
"""
            daily_plans.append({
                "day": day_num,
                "content": daily_content
            })
        
        # Create budget narrative
        budget_narrative = f"""
# Budget Breakdown for Your {destination} Adventure

## Accommodation
* {budget_level.title()} level: ${budget["per_day"]["accommodation"]} per night
* Total for {trip_duration} nights: ${budget["total"]["accommodation"]}

## Food
* Daily budget: ${budget["per_day"]["food"]}
* Total for {trip_duration} days: ${budget["total"]["food"]}

## Transportation
* Daily average: ${budget["per_day"]["transportation"]}
* Total: ${budget["total"]["transportation"]}

## Activities and Attractions
* Daily budget: ${budget["per_day"]["activities"]}
* Total: ${budget["total"]["activities"]}

## Total Trip Cost
* ${budget["total"]["grand_total"]} for your {trip_duration}-day adventure

This budget is based on {budget_level} level travel in {destination}, with a focus on {interests_str}.
"""
        
        return {
            "main_narrative": main_narrative,
            "daily_plans": daily_plans,
            "budget_narrative": budget_narrative
        }