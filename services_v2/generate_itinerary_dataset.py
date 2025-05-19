import os
import csv
import time
import random
import json
import google.generativeai as genai

# ------------------------
# Config
# ------------------------
# Load API key
with open("config.json", "r") as f:
    config = json.load(f)
genai.configure(api_key=config["GEMINI_API_KEY"])

# Gemini model setup
generation_config = {
    "temperature": 0.8,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 1000,
}
safety_settings = [
    {"category": "HARM_CATEGORY_DANGEROUS", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# Preference categories (same as encoder)
CORE_PREFERENCES = [
    "history", "food", "adventure", "culture", "nature",
    "relaxation", "shopping", "nightlife", "family"
]
SPECIALIZED_PREFERENCES = [
    "local_experience", "luxury", "budget_conscious", "accessibility",
    "early_riser", "night_owl", "off_beaten_path", "instagram_worthy",
    "needs_breaks", "sustainable", "vegetarian", "group_activities"
]
EXCLUSIVE_PAIRS = [
    ("luxury", "budget_conscious"),
    ("early_riser", "night_owl"),
    ("off_beaten_path", "instagram_worthy"),
    ("accessibility", "off_beaten_path"),
    ("needs_breaks", "adventure"),
    ("relaxation", "adventure")
]

DESTINATIONS = ["Rome", "Paris", "Bangkok", "New York", "Bali", "Tokyo", "Barcelona", "Istanbul"]
BUDGET_LEVELS = ["low", "medium", "high"]
DURATIONS = [3, 4, 5, 7]

# ------------------------
# Functions
# ------------------------
def are_preferences_compatible(preferences):
    for a, b in EXCLUSIVE_PAIRS:
        if a in preferences and b in preferences:
            return False
    return True

def sample_preferences():
    while True:
        core = random.sample(CORE_PREFERENCES, random.randint(2, 4))
        special = random.sample(SPECIALIZED_PREFERENCES, random.randint(2, 3))
        all_prefs = core + special
        if are_preferences_compatible(all_prefs):
            return core, special

def generate_itinerary(destination, duration, budget, core_prefs, special_prefs):
    prompt = f"""
You are a travel assistant. Generate a detailed itinerary for a traveler visiting {destination} for {duration} days.

Traveler's profile:
- Budget: {budget}
- Core interests: {', '.join(core_prefs)}
- Specialized preferences: {', '.join(special_prefs)}

Instructions:
- Create a separate plan for each day: "Day 1: ...", "Day 2: ..." etc.
- Respect the budget. For example:
  - low → affordable/free attractions, public transport, street food
  - medium → mix of value and comfort (some guided tours, casual restaurants)
  - high → luxury hotels, private experiences, fine dining
- Reflect the preferences in the activity suggestions.
- DO NOT mention the category names (e.g., "since you like food").
- Make it sound helpful, realistic, and like a curated travel itinerary.
"""
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        safety_settings=safety_settings,
    )
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Generation error: {e}")
        time.sleep(2)
        return None

# ------------------------
# Main generation loop
# ------------------------
def generate_itinerary_dataset(n_examples=1000, output_file="itinerary_dataset.csv"):
    with open(output_file, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["destination", "duration", "budget", "core_prefs", "special_prefs", "itinerary"])
        
        count = 0
        attempts = 0
        while count < n_examples and attempts < n_examples * 3:
            attempts += 1

            # Sample input
            destination = random.choice(DESTINATIONS)
            duration = random.choice(DURATIONS)
            budget = random.choice(BUDGET_LEVELS)
            core_prefs, special_prefs = sample_preferences()

            # Generate
            itinerary = generate_itinerary(destination, duration, budget, core_prefs, special_prefs)
            if not itinerary or itinerary.count("Day") < duration:
                continue  # reject low-quality or incomplete outputs

            # Write row
            writer.writerow([
                destination,
                duration,
                budget,
                json.dumps(core_prefs),
                json.dumps(special_prefs),
                itinerary.replace("\n", " ").strip()
            ])
            f.flush()
            count += 1

            if count % 10 == 0:
                print(f"[{count}/{n_examples}] examples generated...")

    print(f"\n✅ Dataset generation complete: {output_file}")

# ------------------------
# Entry point
# ------------------------
if __name__ == "__main__":
    generate_itinerary_dataset(n_examples=1000)
