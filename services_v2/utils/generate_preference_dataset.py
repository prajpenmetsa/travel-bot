import os
import csv
import time
import random
import google.generativeai as genai
from typing import List, Dict, Set, Tuple
import pandas as pd
import json

# Configure Google API key
try:
    GOOGLE_API_KEY = "AIzaSyA2GZGoroN-Mowyi8RDCxkJaO_YhRPJbvI"
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    print(f"Error configuring Google API: {e}")
    exit(1)

# Define standard Gemini model configuration
generation_config = {
    "temperature": 0.9,  # We'll vary this later for diversity
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
    
    # Vary the temperature for diversity
    current_config = generation_config.copy()
    current_config["temperature"] = random.uniform(0.7, 1.0)
    
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
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash-8b",  # Using the Flash model
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

def generate_dataset(num_examples: int = 2000, output_file: str = "preference_dataset.csv"):
    """Generate a full dataset of preference descriptions and their labels"""
    # Create a list to hold the examples
    examples = []
    
    # Create output directories
    data_dir = os.path.dirname(output_file)
    if data_dir and not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    
    # Open CSV for writing progress incrementally
    with open(output_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Write the header
        header = ["description"] + [f"label_{cat}" for cat in PREFERENCE_CATEGORIES]
        writer.writerow(header)
        
        # Generate examples
        count = 0
        attempts = 0
        max_attempts = num_examples * 3  # Allow for more failures
        
        print(f"Generating {num_examples} preference examples...")
        
        while count < num_examples and attempts < max_attempts:
            attempts += 1
            
            # Progress report
            if attempts % 10 == 0:
                print(f"Progress: {count}/{num_examples} examples generated ({attempts} attempts)")
            
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
                
                # 5. Add to our examples list
                examples.append({
                    "description": description,
                    "labels": selected_preferences
                })
                
                count += 1
                
                # Avoid rate limiting - more conservative rate
                time.sleep(1.0)
                
            except Exception as e:
                print(f"Error in generation loop: {e}")
                time.sleep(5)  # Longer wait on error
    
    print(f"Generated {count} examples successfully!")
    
    # Also save as a DataFrame
    df = pd.DataFrame(examples)
    df_path = output_file.replace('.csv', '.pkl')
    df.to_pickle(df_path)
    print(f"Saved DataFrame to {df_path}")
    
    # Generate some statistics
    label_counts = {label: 0 for label in PREFERENCE_CATEGORIES}
    for example in examples:
        for label in example["labels"]:
            label_counts[label] += 1
            
    print("\nLabel Distribution:")
    for label, count in label_counts.items():
        percentage = (count / len(examples)) * 100
        print(f"{label}: {count} ({percentage:.1f}%)")
    
    # Calculate co-occurrence matrix
    print("\nPreference Co-occurrence:")
    co_occurrence = calculate_co_occurrence(examples)
    for pair, count in sorted(co_occurrence.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{pair[0]} + {pair[1]}: {count} times")
        
    return examples

def calculate_co_occurrence(examples: List[Dict]) -> Dict[Tuple[str, str], int]:
    """Calculate how often each pair of preferences co-occurs"""
    co_occurrence = {}
    
    for example in examples:
        labels = example["labels"]
        for i in range(len(labels)):
            for j in range(i+1, len(labels)):
                pair = tuple(sorted([labels[i], labels[j]]))
                co_occurrence[pair] = co_occurrence.get(pair, 0) + 1
                
    return co_occurrence

def analyze_dataset(dataset_path: str):
    """Analyze an existing dataset for label distribution and statistics"""
    if dataset_path.endswith('.pkl'):
        df = pd.read_pickle(dataset_path)
        # Extract all unique labels
        all_labels = set()
        for labels in df['labels']:
            all_labels.update(labels)
        
        # Count label frequencies
        label_counts = {label: 0 for label in PREFERENCE_CATEGORIES}
        for labels in df['labels']:
            for label in labels:
                label_counts[label] += 1
    else:
        df = pd.read_csv(dataset_path)
        label_columns = [col for col in df.columns if col.startswith('label_')]
        
        # Count label frequencies
        label_counts = {}
        for col in label_columns:
            label = col.replace('label_', '')
            count = df[col].sum()
            label_counts[label] = count
    
    # Print statistics
    print("\nDataset Analysis")
    print(f"Total examples: {len(df)}")
    print("\nLabel Distribution:")
    for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(df)) * 100
        print(f"{label}: {count} ({percentage:.1f}%)")
    
    # Calculate average labels per example
    if 'labels' in df.columns:
        avg_labels = sum(len(labels) for labels in df['labels']) / len(df)
    else:
        avg_labels = sum(df[label_columns].sum(axis=1)) / len(df)
        
    print(f"\nAverage labels per example: {avg_labels:.2f}")
    
    # Print some example descriptions
    print("\nSample Examples:")
    for i in range(min(3, len(df))):
        print(f"\nExample {i+1}:")
        print(f"Description: {df['description'].iloc[i]}")
        if 'labels' in df.columns:
            print(f"Labels: {', '.join(df['labels'].iloc[i])}")
        else:
            labels = [col.replace('label_', '') for col in label_columns if df[col].iloc[i] == 1]
            print(f"Labels: {', '.join(labels)}")

if __name__ == "__main__":
    # Set output path - make sure 'data' directory exists
    os.makedirs("data", exist_ok=True)
    dataset_path = os.path.join("data", "preference_dataset.csv")
    
    # Check if we should analyze an existing dataset or generate a new one
    if os.path.exists(dataset_path) and input("Dataset already exists. Analyze existing dataset? (y/n) ").lower() == 'y':
        analyze_dataset(dataset_path)
    else:
        # Generate the dataset
        examples = generate_dataset(num_examples=2000, output_file=dataset_path)
        
        print(f"\nDataset generated successfully! Saved to {dataset_path}")
        print("Sample examples:")
        for i in range(min(3, len(examples))):
            print(f"\nExample {i+1}:")
            print(f"Description: {examples[i]['description']}")
            print(f"Labels: {', '.join(examples[i]['labels'])}")