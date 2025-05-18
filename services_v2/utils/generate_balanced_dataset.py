import os
import csv
import time
import random
import json
import google.generativeai as genai
from typing import List, Dict, Set, Tuple, Counter
import pandas as pd
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize

# Download NLTK resources if needed
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

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
    "temperature": 0.8,
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

def sample_balanced_preferences(class_counts: Dict[str, int], min_target: int = 250, max_attempts: int = 10) -> List[str]:
    """
    Generate preferences with focus on underrepresented classes
    
    Parameters:
    -----------
    class_counts: Dict[str, int]
        Current count of each class in the dataset
    min_target: int
        Minimum target count for each class
    max_attempts: int
        Maximum number of recursive attempts to find compatible preferences
        
    Returns:
    --------
    List[str]
        Selected preferences
    """
    # Exit condition for recursion to prevent maximum recursion depth
    if max_attempts <= 0:
        # Fallback to a simple safe set of preferences
        return [random.choice(CORE_PREFERENCES), random.choice(SPECIALIZED_PREFERENCES)]
    
    # Identify underrepresented classes
    underrepresented = {
        cat: count for cat, count in class_counts.items() if count < min_target
    }
    
    # Sort from least to most represented
    sorted_underrepresented = sorted(underrepresented.items(), key=lambda x: x[1])
    
    # Make sure we select at least one core preference and one specialized preference
    selected_prefs = []
    
    # First, try to select an underrepresented core preference
    core_options = [cat for cat, _ in sorted_underrepresented if cat in CORE_PREFERENCES]
    if core_options:
        # Prioritize the most underrepresented core preference
        selected_prefs.append(core_options[0])
    else:
        # If all core preferences have met the target, pick one randomly
        selected_prefs.append(random.choice(CORE_PREFERENCES))
    
    # Next, try to select an underrepresented specialized preference
    specialized_options = [cat for cat, _ in sorted_underrepresented if cat in SPECIALIZED_PREFERENCES]
    if specialized_options:
        # Prioritize the most underrepresented specialized preference
        selected_prefs.append(specialized_options[0])
    else:
        # If all specialized preferences have met the target, pick one randomly
        selected_prefs.append(random.choice(SPECIALIZED_PREFERENCES))
    
    # Now add 2-3 more preferences, prioritizing underrepresented ones
    remaining_to_add = random.randint(2, 3)
    underrep_list = [cat for cat, _ in sorted_underrepresented if cat not in selected_prefs]
    
    for _ in range(remaining_to_add):
        if underrep_list:
            # Pick from underrepresented categories
            next_pref = underrep_list.pop(0)
            selected_prefs.append(next_pref)
        else:
            # If we've exhausted underrepresented categories, pick randomly
            remaining_cats = [cat for cat in PREFERENCE_CATEGORIES 
                             if cat not in selected_prefs]
            if not remaining_cats:
                break
            selected_prefs.append(random.choice(remaining_cats))
    
    # Check compatibility and retry if needed
    if not are_preferences_compatible(selected_prefs):
        # Decrement max_attempts to prevent infinite recursion
        return sample_balanced_preferences(class_counts, min_target, max_attempts - 1)
    
    return selected_prefs

def generate_preference_description(preferences: List[str], target_length: int = 65) -> str:
    """
    Generate a synthetic preference description using Gemini API
    
    Parameters:
    -----------
    preferences: List[str]
        List of preferences to include
    target_length: int
        Target token length (to match dataset statistics)
    """
    # Prepare the preference list for the prompt
    core_selected = [p for p in preferences if p in CORE_PREFERENCES]
    specialized_selected = [p for p in preferences if p in SPECIALIZED_PREFERENCES]
    
    # Vary the temperature for diversity, but within a narrower range for consistency
    current_config = generation_config.copy()
    current_config["temperature"] = random.uniform(0.7, 0.9)
    
    # Create a custom prompt with selected preferences
    custom_prompt = f"""
Create a natural-sounding traveler preference description in first person that clearly expresses the following preferences:

CORE PREFERENCES TO INCLUDE:
{', '.join(core_selected)}

SPECIALIZED PREFERENCES TO INCLUDE:
{', '.join(specialized_selected)}

Your response should:
1. Be about 2-3 sentences (around {target_length} words)
2. Include clear indicators of all the selected preferences
3. Sound like something a real traveler would say
4. NOT explicitly name the preference categories (don't say "I'm budget_conscious")

Only output the traveler preference description with no additional text or explanation.
"""
    
    # Initialize the model with current configuration
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
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
        time.sleep(2)
        return None

def count_tokens_and_sentences(description: str) -> Tuple[int, int]:
    """Count the tokens and sentences in a description"""
    if not description:
        return 0, 0
    
    tokens = word_tokenize(description)
    sentences = sent_tokenize(description)
    return len(tokens), len(sentences)

def analyze_dataset(dataset_path: str) -> Dict[str, object]:
    """
    Analyze an existing dataset for class distribution and statistics
    
    Returns:
    --------
    Dict with analysis results
    """
    print(f"Analyzing dataset: {dataset_path}")
    
    # Check if file exists
    if not os.path.exists(dataset_path):
        print(f"Error: File {dataset_path} not found")
        return {}
    
    # Initialize results
    results = {
        "total_examples": 0,
        "class_counts": {},
        "token_stats": {},
        "sentence_stats": {}
    }
    
    # Read the CSV file
    try:
        df = pd.read_csv(dataset_path)
        results["total_examples"] = len(df)
        
        # Get descriptions
        descriptions = df["description"].tolist()
        
        # Calculate token and sentence statistics
        token_counts = []
        sentence_counts = []
        for desc in descriptions:
            tokens, sentences = count_tokens_and_sentences(desc)
            token_counts.append(tokens)
            sentence_counts.append(sentences)
        
        results["token_stats"] = {
            "max": max(token_counts),
            "min": min(token_counts),
            "avg": sum(token_counts) / len(token_counts),
            "distribution": Counter([min(100, (t // 10) * 10) for t in token_counts])
        }
        
        results["sentence_stats"] = {
            "max": max(sentence_counts),
            "min": min(sentence_counts),
            "avg": sum(sentence_counts) / len(sentence_counts)
        }
        
        # Count class frequencies
        label_columns = [col for col in df.columns if col.startswith("label_")]
        class_counts = {}
        for col in label_columns:
            class_name = col.replace("label_", "")
            class_counts[class_name] = df[col].sum()
        
        results["class_counts"] = class_counts
        
        # Print summary
        print(f"\nDataset Analysis:")
        print(f"Total examples: {results['total_examples']}")
        print("\nToken statistics:")
        print(f"  Max: {results['token_stats']['max']}")
        print(f"  Min: {results['token_stats']['min']}")
        print(f"  Avg: {results['token_stats']['avg']:.2f}")
        
        print("\nSentence statistics:")
        print(f"  Max: {results['sentence_stats']['max']}")
        print(f"  Min: {results['sentence_stats']['min']}")
        print(f"  Avg: {results['sentence_stats']['avg']:.2f}")
        
        print("\nClass counts:")
        for class_name, count in sorted(results["class_counts"].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / results["total_examples"]) * 100
            print(f"  {class_name}: {count} ({percentage:.2f}%)")
        
        return results
        
    except Exception as e:
        print(f"Error analyzing dataset: {e}")
        return {}

def generate_balanced_dataset(dataset_path: str, 
                            min_class_target: int = 250,
                            max_new_examples: int = 2000,
                            incremental_save: int = 50):
    """
    Continue generating examples with a focus on class balance
    
    Parameters:
    -----------
    dataset_path: str
        Path to the existing dataset CSV file
    min_class_target: int
        Minimum number of examples for each class
    max_new_examples: int
        Maximum number of new examples to generate
    incremental_save: int
        How often to save progress to a backup file
    """
    # First, analyze the dataset
    analysis = analyze_dataset(dataset_path)
    if not analysis:
        return
    
    current_count = analysis["total_examples"]
    class_counts = analysis["class_counts"]
    avg_tokens = analysis["token_stats"]["avg"]
    avg_sentences = analysis["sentence_stats"]["avg"]
    
    print(f"\nStarting balanced dataset generation:")
    print(f"Current example count: {current_count}")
    print(f"Target minimum per class: {min_class_target}")
    
    # Calculate approximately how many more examples we need
    classes_below_target = [cls for cls, count in class_counts.items() if count < min_class_target]
    examples_needed = sum([min_class_target - class_counts[cls] for cls in classes_below_target])
    
    print(f"Classes below target: {len(classes_below_target)}/{len(PREFERENCE_CATEGORIES)}")
    print(f"Approximately {examples_needed} more examples needed to reach class balance")
    
    # Cap the number of new examples
    examples_to_generate = min(examples_needed, max_new_examples)
    print(f"Will generate up to {examples_to_generate} new examples")
    
    # Load the header
    with open(dataset_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)  # Get header row
    
    # Create a backup of the existing file
    backup_path = dataset_path.replace('.csv', f'_backup_{current_count}.csv')
    os.system(f"cp {dataset_path} {backup_path}")
    print(f"Created backup at {backup_path}")
    
    # Open the original file in append mode
    with open(dataset_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Also create an incremental backup file
        incremental_backup_path = dataset_path.replace('.csv', '_balanced_backup.csv')
        incremental_backup_file = open(incremental_backup_path, 'w', newline='', encoding='utf-8')
        incremental_writer = csv.writer(incremental_backup_file)
        incremental_writer.writerow(header)
        
        # Track new examples for our DataFrame
        new_examples = []
        
        # Generate examples
        attempts = 0
        new_count = 0
        max_attempts = examples_to_generate * 3  # Allow for failures
        
        while new_count < examples_to_generate and attempts < max_attempts:
            attempts += 1
            
            # Progress report
            if attempts % 5 == 0:
                print(f"Progress: {new_count}/{examples_to_generate} new examples ({attempts} attempts)")
            
            try:
                # 1. Generate balanced preferences
                selected_preferences = sample_balanced_preferences(class_counts, min_class_target)
                
                # 2. Generate a description targeting the average length
                description = generate_preference_description(selected_preferences, int(avg_tokens))
                if not description:
                    continue
                
                # 3. Verify the description quality
                tokens, sentences = count_tokens_and_sentences(description)
                if tokens < 30 or tokens > 120 or sentences < 1 or sentences > 4:
                    print(f"Skipping description outside normal range (tokens: {tokens}, sentences: {sentences})")
                    continue
                
                # 4. Create binary encoding for CSV
                label_encoding = [1 if cat in selected_preferences else 0 for cat in PREFERENCE_CATEGORIES]
                
                # 5. Write to CSV
                row = [description] + label_encoding
                writer.writerow(row)
                f.flush()  # Ensure it's written to disk
                
                # 6. Add to our examples list
                new_examples.append({
                    "description": description,
                    "labels": selected_preferences,
                    "tokens": tokens,
                    "sentences": sentences
                })
                
                # 7. Write to incremental backup
                incremental_writer.writerow(row)
                incremental_backup_file.flush()
                
                # 8. Update class counts
                for pref in selected_preferences:
                    class_counts[pref] += 1
                
                new_count += 1
                
                # Save a DataFrame snapshot at regular intervals
                if new_count % incremental_save == 0:
                    mini_df = pd.DataFrame(new_examples)
                    mini_df_path = dataset_path.replace('.csv', f'_balanced_new_{new_count}.pkl')
                    mini_df.to_pickle(mini_df_path)
                    print(f"Saved interim progress: {new_count} new examples")
                    
                    # Quick class distribution update
                    print("Updated class counts for underrepresented classes:")
                    sorted_counts = sorted(class_counts.items(), key=lambda x: x[1])
                    for cls, count in sorted_counts[:5]:
                        print(f"  {cls}: {count}")
                
                # Avoid rate limiting
                time.sleep(1.5)
                
            except Exception as e:
                print(f"Error in generation loop: {e}")
                time.sleep(5)
        
        # Close the incremental backup
        incremental_backup_file.close()
        
        print(f"\nGenerated {new_count} additional balanced examples successfully!")
        print(f"Total dataset now contains {current_count + new_count} examples")
        
        # Save the new examples as a separate DataFrame for analysis
        if new_examples:
            new_df = pd.DataFrame(new_examples)
            new_df_path = dataset_path.replace('.csv', '_balanced_examples.pkl')
            new_df.to_pickle(new_df_path)
            print(f"Saved new examples to {new_df_path}")
            
            # Generate statistics for new examples
            token_avg = sum(ex["tokens"] for ex in new_examples) / len(new_examples)
            sentence_avg = sum(ex["sentences"] for ex in new_examples) / len(new_examples)
            
            print("\nNew Examples Statistics:")
            print(f"Average tokens: {token_avg:.2f}")
            print(f"Average sentences: {sentence_avg:.2f}")
            
            # Calculate class distribution in new examples
            new_class_counts = {label: 0 for label in PREFERENCE_CATEGORIES}
            for example in new_examples:
                for label in example["labels"]:
                    new_class_counts[label] += 1
                        
            print("\nLabel Distribution in New Examples:")
            for label, count in sorted(new_class_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(new_examples)) * 100
                print(f"{label}: {count} ({percentage:.1f}%)")
            
            # Show some examples
            print("\nSample New Examples:")
            for i in range(min(3, len(new_examples))):
                print(f"\nExample {i+1}:")
                print(f"Description: {new_examples[i]['description']}")
                print(f"Labels: {', '.join(new_examples[i]['labels'])}")
                print(f"Tokens: {new_examples[i]['tokens']}, Sentences: {new_examples[i]['sentences']}")
        
        # Final analysis of the whole dataset
        print("\nFinal dataset analysis:")
        analyze_dataset(dataset_path)

if __name__ == "__main__":
    # Set path to existing dataset
    dataset_path = os.path.join("data", "preference_dataset.csv")
    
    # Generate balanced dataset
    generate_balanced_dataset(
        dataset_path=dataset_path,
        min_class_target=250,  # Ensure each class has at least 250 examples
        max_new_examples=2000,  # Cap at 2000 new examples
        incremental_save=50     # Save progress every 50 examples
    )