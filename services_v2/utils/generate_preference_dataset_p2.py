import os
import csv
import time
import random
import json
import google.generativeai as genai
from typing import List, Dict, Set, Tuple
import pandas as pd

# Load the config file to get the API key
try:
    with open("../config.json", "r") as f:
        config = json.load(f)
    GOOGLE_API_KEY = config.get("GEMINI_API_KEY")
    if not GOOGLE_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in config.json")
    genai.configure(api_key=GOOGLE_API_KEY)
    print(f"Successfully configured Gemini API with key from config.json")
except Exception as e:
    print(f"Error loading config or configuring Gemini API: {e}")
    exit(1)

# Define standard Gemini model configuration
generation_config = {
    "temperature": 0.8,  # Slightly lower temperature for consistency
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 300,
}

safety_settings = [
    {"category": "HARM_CATEGORY_DANGEROUS", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# Define preference categories
CORE_PREFERENCES = [
    "history", "food", "adventure", "culture", "nature", 
    "relaxation", "shopping", "nightlife", "family"
]

SPECIALIZED_PREFERENCES = [
    "local_experience", "luxury", "budget_conscious", "accessibility",
    "early_riser", "night_owl", "off_beaten_path", "instagram_worthy",
    "needs_breaks", "sustainable", "vegetarian", "group_activities"
]

# All preference categories combined
PREFERENCE_CATEGORIES = CORE_PREFERENCES + SPECIALIZED_PREFERENCES

# Define mutually exclusive preferences
EXCLUSIVE_PAIRS = [
    ("luxury", "budget_conscious"),
    ("early_riser", "night_owl"),
    ("off_beaten_path", "instagram_worthy"),
    ("accessibility", "off_beaten_path"),
    ("needs_breaks", "adventure"),
    ("relaxation", "adventure")
]

def are_preferences_compatible(preferences: List[str]) -> bool:
    """Check if a set of preferences contains any mutually exclusive pairs"""
    for pair in EXCLUSIVE_PAIRS:
        if pair[0] in preferences and pair[1] in preferences:
            return False
    return True

def sample_random_preferences() -> List[str]:
    """Generate a random set of compatible preferences"""
    # Choose 2-4 core preferences
    num_core = random.randint(2, 4)
    core_prefs = random.sample(CORE_PREFERENCES, num_core)
    
    # Choose 2-3 specialized preferences
    num_specialized = random.randint(2, 3)
    specialized_prefs = random.sample(SPECIALIZED_PREFERENCES, num_specialized)
    
    # Combine them
    all_prefs = core_prefs + specialized_prefs
    
    # Check if they're compatible; if not, try again
    if not are_preferences_compatible(all_prefs):
        return sample_random_preferences()
    
    return all_prefs

def generate_preference_description(preferences: List[str]) -> str:
    """Generate a synthetic preference description using Gemini API"""
    # Prepare the preference list for the prompt
    core_selected = [p for p in preferences if p in CORE_PREFERENCES]
    specialized_selected = [p for p in preferences if p in SPECIALIZED_PREFERENCES]
    
    # Vary the temperature for diversity, but within a narrower range for consistency
    current_config = generation_config.copy()
    current_config["temperature"] = random.uniform(0.7, 0.9)  # Narrower range
    
    # Create a custom prompt with selected preferences
    custom_prompt = f"""
Create a natural-sounding traveler preference description in first person that clearly expresses the following preferences:

CORE PREFERENCES TO INCLUDE:
{', '.join(core_selected)}

SPECIALIZED PREFERENCES TO INCLUDE:
{', '.join(specialized_selected)}

Your response should:
1. Be 2-4 sentences in natural conversational language
2. Include clear indicators of all the selected preferences
3. Sound like something a real traveler would say
4. Vary in length, style, and complexity
5. NOT explicitly name the preference categories (don't say "I'm budget_conscious")

Only output the traveler preference description with no additional text or explanation.
"""
    
    # Initialize the model with current configuration
    # Use gemini-1.5-flash (same model as narrative_service)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",  # Using the same model as narrative_service
        generation_config=current_config,
        safety_settings=safety_settings,
    )
    
    # Generate the response
    try:
        response = model.generate_content(custom_prompt)
        description = response.text.strip()
        return description
    except Exception as e:
        print(f"Error generating description: {e}")
        # Wait a moment before retrying in case of rate limits
        time.sleep(2)
        return None

def continue_dataset_generation(dataset_path: str, 
                              target_total: int = 2000, 
                              incremental_save: int = 50):
    """
    Continue generating examples from where we left off
    
    Parameters:
    -----------
    dataset_path: str
        Path to the existing dataset CSV file
    target_total: int
        Total number of examples to reach
    incremental_save: int
        How often to save progress to a backup file
    """
    # First check if the file exists
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset file {dataset_path} not found")
        return
    
    # Load existing examples
    try:
        # Read CSV to get the headers and count
        with open(dataset_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)  # Get header row
            existing_examples = list(reader)  # Read all existing examples
        
        current_count = len(existing_examples)
        print(f"Found {current_count} existing examples in {dataset_path}")
        
        if current_count >= target_total:
            print(f"Already have {current_count} examples, which meets or exceeds the target of {target_total}")
            return
        
        # Create a backup of the existing file
        backup_path = dataset_path.replace('.csv', f'_backup_{current_count}.csv')
        with open(backup_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(existing_examples)
        print(f"Created backup at {backup_path}")
        
        # Open the original file in append mode
        with open(dataset_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Also create an incremental backup file that we'll update regularly
            incremental_backup_path = dataset_path.replace('.csv', '_incremental_backup.csv')
            incremental_backup_file = open(incremental_backup_path, 'w', newline='', encoding='utf-8')
            incremental_writer = csv.writer(incremental_backup_file)
            incremental_writer.writerow(header)
            
            # Track new examples for our DataFrame
            new_examples = []
            
            # Generate examples
            remaining = target_total - current_count
            attempts = 0
            new_count = 0
            max_attempts = remaining * 3  # Allow more failures
            
            print(f"Continuing dataset generation: {remaining} more examples needed")
            
            while new_count < remaining and attempts < max_attempts:
                attempts += 1
                
                # Progress report
                if attempts % 5 == 0:
                    print(f"Progress: {new_count}/{remaining} new examples generated ({attempts} attempts)")
                
                try:
                    # 1. Generate random preferences
                    selected_preferences = sample_random_preferences()
                    
                    # 2. Generate a description using these preferences
                    description = generate_preference_description(selected_preferences)
                    if not description:
                        continue
                    
                    # 3. Create binary encoding for CSV
                    label_encoding = [1 if cat in selected_preferences else 0 for cat in PREFERENCE_CATEGORIES]
                    
                    # 4. Write to CSV
                    row = [description] + label_encoding
                    writer.writerow(row)
                    f.flush()  # Ensure it's written to disk
                    
                    # 5. Add to our examples list
                    new_examples.append({
                        "description": description,
                        "labels": selected_preferences
                    })
                    
                    # Write to incremental backup
                    incremental_writer.writerow(row)
                    incremental_backup_file.flush()
                    
                    new_count += 1
                    
                    # Save a DataFrame snapshot at regular intervals
                    if new_count % incremental_save == 0:
                        # Create a mini DataFrame with just the new examples
                        mini_df = pd.DataFrame(new_examples)
                        mini_df_path = dataset_path.replace('.csv', f'_new_{new_count}.pkl')
                        mini_df.to_pickle(mini_df_path)
                        print(f"Saved interim progress: {new_count} new examples")
                    
                    # Avoid rate limiting - more conservative rate
                    time.sleep(1.5)  # Slightly longer pause
                    
                except Exception as e:
                    print(f"Error in generation loop: {e}")
                    time.sleep(5)  # Longer wait on error
            
            # Close the incremental backup
            incremental_backup_file.close()
            
            print(f"Generated {new_count} additional examples successfully!")
            print(f"Total dataset now contains {current_count + new_count} examples")
            
            # Save the new examples as a separate DataFrame for analysis
            if new_examples:
                new_df = pd.DataFrame(new_examples)
                new_df_path = dataset_path.replace('.csv', '_new_examples.pkl')
                new_df.to_pickle(new_df_path)
                print(f"Saved new examples to {new_df_path}")
                
                # Generate statistics for new examples
                label_counts = {label: 0 for label in PREFERENCE_CATEGORIES}
                for example in new_examples:
                    for label in example["labels"]:
                        label_counts[label] += 1
                        
                print("\nLabel Distribution in New Examples:")
                for label, count in label_counts.items():
                    percentage = (count / len(new_examples)) * 100
                    print(f"{label}: {count} ({percentage:.1f}%)")
                
                # Show some examples
                print("\nSample New Examples:")
                for i in range(min(3, len(new_examples))):
                    print(f"\nExample {i+1}:")
                    print(f"Description: {new_examples[i]['description']}")
                    print(f"Labels: {', '.join(new_examples[i]['labels'])}")
            
    except Exception as e:
        print(f"Error during dataset continuation: {e}")

if __name__ == "__main__":
    # Set path to existing dataset
    dataset_path = os.path.join("data", "preference_dataset.csv")
    
    # Continue generating examples
    continue_dataset_generation(
        dataset_path=dataset_path, 
        target_total=2000,
        incremental_save=50
    )