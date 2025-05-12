"""
Narrative generation service for travel itineraries.
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
    """Service for generating travel narratives and itinerary text."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the narrative service with API key for AI models.
        
        Parameters:
        -----------
        api_key : str
            API key for AI text generation service (e.g., Gemini)
        """
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
        """
        Generate a complete narrative for the travel itinerary.
        
        Parameters:
        -----------
        destination : str
            The city or location name
        interests : list
            List of interest categories (e.g., ["food", "history", "art"])
        budget_level : str
            "low", "medium", or "high"
        trip_duration : int
            Number of days for the trip
        experiences : list
            List of experience dictionaries
        budget : dict
            Budget breakdown dictionary
            
        Returns:
        --------
        dict
            Narrative content including main narrative, daily plans, and budget breakdown
        """
        
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
        
        # Create directory if it doesn't exist
        output_dir = Path("Generated_files")
        output_dir.mkdir(exist_ok=True)
        
        # Save to file - fix the path to use the actual filename variable
        file_path = output_dir / filename
        file_path.write_text(md_content)
        
        return filename
    
    def _generate_fallback_narrative(self, 
                                   destination: str, 
                                   interests: List[str], 
                                   budget_level: str, 
                                   trip_duration: int,
                                   experiences: Dict[str, Any],
                                   budget: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a narrative using fallback method (e.g., template-based).
        
        This is used when the AI model is not available or fails.
        """
        # Handle different budget formats
        if isinstance(budget, dict) and "total" in budget and isinstance(budget["total"], dict):
            budget_total = budget["total"].get("grand_total", 0)
        elif isinstance(budget, dict) and "total" in budget and isinstance(budget["total"], (int, float)):
            budget_total = budget["total"]
        elif isinstance(budget, (int, float)):
            budget_total = budget
        else:
            budget_total = 0
        
        main_narrative = (
            f"Explore {destination} in {trip_duration} days of {budget_level} travel, "
            f"focusing on {', '.join(interests)}. Experience the highlights and hidden gems "
            f"with a budget-friendly approach."
        )
        
        daily_plans = []
        for day in range(1, trip_duration + 1):
            content = (
                f"Day {day}: Discover the best of {destination}. Enjoy local attractions, "
                f"cuisine, and culture. Stay within your budget and have an amazing experience."
            )
            daily_plans.append({"day": day, "content": content})
        
        budget_narrative = (
            f"Estimated budget for {trip_duration} days: ${budget_total}. This includes "
            f"accommodation, food, activities, and transportation."
        )
        
        return {
            "main_narrative": main_narrative,
            "daily_plans": daily_plans,
            "budget_narrative": budget_narrative
        }