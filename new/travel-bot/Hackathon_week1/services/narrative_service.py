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
            model = genai.GenerativeModel('gemini-2.0-flash')
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
            
            # narrative dictionary
            narrative_dict = {
                "main_narrative": narrative,
                "daily_plans": daily_plans,
                "budget_narrative": budget_narrative
            }

            # Save as markdown file
            md_filename = self.save_itinerary_as_md(destination, trip_duration, budget_level, narrative_dict)
            narrative_dict["md_filename"] = md_filename

            return narrative_dict
        
        except Exception as e:
            logger.error(f"Error generating narrative with Gemini: {e}")
            # return self._generate_fallback_narrative(
            #     destination, interests, budget_level, trip_duration, experiences, budget
            # )
    
    def save_itinerary_as_md(self, destination: str, trip_duration: int, budget_level: str, 
                    narrative: Dict[str, Any]) -> str:
        """Save the itinerary as a Markdown file and return the filename."""
        from pathlib import Path
        
        # Create a clean filename from the destination
        filename = f"itinerary_{destination.replace(' ', '_')}_{trip_duration}days.md"
        
        # Combine all narratives into one markdown document
        md_content = f"# {trip_duration}-DAY {budget_level.upper()} ADVENTURE IN {destination.upper()}\n\n"
        md_content += narrative["main_narrative"]
        
        # Add day-by-day itinerary
        md_content += "\n\n## DAY-BY-DAY ITINERARY\n"
        for day_plan in narrative["daily_plans"]:
            md_content += f"\n### DAY {day_plan['day']}\n"
            md_content += f"\n{day_plan['content']}\n"
        
        # Add budget breakdown
        md_content += "\n\n## BUDGET BREAKDOWN\n\n"
        md_content += narrative["budget_narrative"]
        
        # Save to file
        file_path = Path(filename)
        file_path.write_text(md_content)
        
        return filename