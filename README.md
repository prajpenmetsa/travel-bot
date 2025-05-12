# Travel-Itinerary-Pitcher ✈️

Generate a multi-day travel plan, realistic budget, narrative write-up, an
AI-evaluated quality score **and** chat with a Gemini-powered assistant about
your itinerary – all from one code-base.

# Project file structure
```bash
services/
├─ app_core.py              ← top-level pipeline & API
├─ budget_service.py
├─ evaluation_service.py
├─ experience_service.py
├─ itinerary_chat_service.py
├─ location_service.py
├─ narrative_service.py
├─ preference_service.py
├─ streamlit_app.py         ← web UI entry point
├─ main.py                  ← CLI entry point
└─ data/…                   ← destinations.json, location_cache.json
└─ saved_itineraries/…      ← saved itineraries stored as json files
└─ generated_files/…        ← generated itineraries stored as md files
└─ generated_files/…        ← generated itineraries stored as md files
  ├─ init.py
  ├─ prompts.py             ← templates for prompts to be used with the Gemini AI API
└─ tests/… 
  └─ fixtures/… 
  └─ integration/… 
  └─ unit/… 
diagrams/
├─ container-diagram.png
├─ context-diagram.png
├─ sequence-diagram.png
Walkthrough_Hackathon1.pdf
req.md                      ← requirements specifications document
README.md
```

# Install dependencies
```bash
pip install streamlit
pip install pydantic
pio install google.generativeai
pip install bs4
```

# Run the program
- from the project root "travel-bot"
```bash
cd services
streamlit run streamlit_app.py
```

# Streamlit UI flow
1. Pick or type a destination(using other) → choose interests, budget level, trip length

2. Click Generate

3. View Itinerary
- narrative write-up
- day-by-day plan
- budget breakdown

4. Provides a quality score

5. Save itinerary if necesary, type any name you want

6. Ask the itinerary AI chat panel

7. Will save as JSON locally and reopen later from the sidebar

# Chat workflow
**app_core.generate_itinerary()** calls **ItineraryChatService.start_session()** and returns a **chat_id**.

- Streamlit stores the id; every user question triggers ask_itinerary_chat(chat_id, message).

- The chat service builds a Gemini prompt that includes:
  - full itinerary text
  - scraped supporting web content
  - the most recent Q&A exchanges and returns a contextual answer

# Scoring Rubric
--------------

Metric               | Weight | How it’s measured
---------------------|--------|--------------------------------------------------------------
Interest coverage    | 25 %   | Percentage of user-selected interests in daily plans
Daily pacing         | 15 %   | Ideal 3–6 activities per day
Diversity            | 10 %   | Ratio of unique activity categories vs. repeats
Budget realism       | 20 %   | Narrative grand total vs. algorithmic grand total
Region realism       | 10 %   | Daily cost compared with destination baseline table
Narrative quality    | 10 %   | Gemini clarity / engagement rating (1–5)
Feasibility          | 10 %   | Placeholder score (0.5) – upgrade with open-hour checks
