"""
Templates for prompts to be used with the Gemini AI API.
"""

NARRATIVE_PROMPT_TEMPLATE = """
You are an expert travel writer and planner. Your task is to create a compelling travel narrative 
for a trip to {destination} that matches the following preferences:

- Interests: {interests}
- Budget level: {budget_level}
- Trip duration: {days} days
- Points of interest to include: {points_of_interest}

Create a persuasive travel "pitch" written in an engaging, narrative style that tells a story about this trip.
Include the following components:
1. A compelling introduction that captures the essence of this destination for this specific traveler
2. A day-by-day breakdown of activities that flows naturally and matches the traveler's interests
3. Budget information showing approximate costs for:
   - Accommodations (per night)
   - Food (per day)
   - Transportation (total for trip)
   - Activities (total for trip)
   - Total trip cost
   
The tone should be personal, exciting, and should highlight unique experiences rather than just listing attractions.
For budget level, use these guidelines:
- Budget: Hostels, street food, public transportation, free/inexpensive activities
- Moderate: 3-star hotels, casual restaurants, mix of public/private transportation, some paid attractions
- Luxury: 4-5 star hotels, fine dining, private transportation, exclusive experiences

Format the response in markdown with clear headings and sections.
"""

DAY_PLAN_PROMPT_TEMPLATE = """
You are an expert travel planner. Create a detailed day-by-day itinerary for Day {day_number} of a {days_total} day trip to {destination}. 
The traveler is interested in: {interests} and has a {budget_level} budget.

The plan should include:
- Morning activity
- Lunch recommendation
- Afternoon activity
- Dinner recommendation
- Evening activity (if appropriate)

Include specific names of attractions, restaurants, or experiences with a brief description of each. 
Each activity and meal should be appropriate for the budget level and align with at least one of the traveler's interests.

Format the response as markdown with time blocks and short, vibrant descriptions.
"""

BUDGET_PROMPT_TEMPLATE = """
You are a travel budget specialist. Create a reasonable budget breakdown for a {days} day trip to {destination} at a {budget_level} travel level.
The traveler is interested in: {interests}.

Provide daily and total estimates for:
1. Accommodation
2. Food (breakfast, lunch, dinner)
3. Local transportation
4. Activities and attractions
5. Miscellaneous expenses

Be specific with currency amounts in local currency and USD equivalent. Base your estimates on real-world prices, and explain any assumptions you've made.
Format the response in a clear, tabular style using markdown.
"""