import pandas as pd
import numpy as np
import re
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize

# Download necessary NLTK data
nltk.download("punkt", quiet=True)


def analyze_dataset(csv_file):
    """
    Analyzes a CSV dataset containing travel preferences with descriptions and multiple labels.

    Args:
        csv_file: Path to the CSV file

    Returns:
        A dictionary containing various analysis results
    """
    # Read the CSV file
    df = pd.read_csv(csv_file)

    # Get the number of examples
    num_examples = len(df)

    # Analyze description text
    descriptions = df["description"].astype(str)

    # Tokenize the descriptions
    description_tokens = [word_tokenize(desc.lower()) for desc in descriptions]
    token_lengths = [len(tokens) for tokens in description_tokens]

    # Calculate token statistics
    max_tokens = max(token_lengths)
    min_tokens = min(token_lengths)
    avg_tokens = sum(token_lengths) / len(token_lengths)

    # Analyze sentence lengths
    sentence_counts = [len(sent_tokenize(desc)) for desc in descriptions]
    max_sentences = max(sentence_counts)
    min_sentences = min(sentence_counts)
    avg_sentences = sum(sentence_counts) / len(sentence_counts)

    # Calculate average words per sentence
    words_per_sentence = []
    for desc in descriptions:
        sentences = sent_tokenize(desc)
        if sentences:
            words = sum(len(word_tokenize(sent)) for sent in sentences)
            words_per_sentence.append(words / len(sentences))

    avg_words_per_sentence = (
        sum(words_per_sentence) / len(words_per_sentence) if words_per_sentence else 0
    )

    # Get label columns (excluding description column)
    label_columns = df.columns[1:]

    # Count examples for each class
    class_counts = {}
    for label in label_columns:
        if label.startswith("label_"):
            class_counts[label] = df[label].sum()

    # Most common label combinations
    # Create a string representation of each row's labels
    label_combinations = []
    for _, row in df.iterrows():
        active_labels = [col[6:] for col in label_columns if row[col] == 1]
        if active_labels:
            label_combinations.append(", ".join(active_labels))

    if label_combinations:
        combo_counts = pd.Series(label_combinations).value_counts().head(10)
    else:
        combo_counts = pd.Series()

    # Return all analysis results
    return {
        "num_examples": num_examples,
        "token_stats": {"max": max_tokens, "min": min_tokens, "avg": avg_tokens},
        "sentence_stats": {
            "max": max_sentences,
            "min": min_sentences,
            "avg": avg_sentences,
            "avg_words_per_sentence": avg_words_per_sentence,
        },
        "class_counts": class_counts,
        "top_combinations": combo_counts,
    }


def write_analysis_to_file(analysis_results, output_file,csv_file):
    """
    Writes the analysis results to a text file.

    Args:
        analysis_results: Dictionary containing analysis results
        output_file: Path to the output text file
    """
    with open(output_file, "w") as f:
        f.write("=== TRAVEL DATASET ANALYSIS ===\n\n")

        f.write(f"Total number of examples: {analysis_results['num_examples']}\n\n")

        f.write("=== TOKEN STATISTICS ===\n")
        f.write(
            f"Maximum tokens in a description: {analysis_results['token_stats']['max']}\n"
        )
        f.write(
            f"Minimum tokens in a description: {analysis_results['token_stats']['min']}\n"
        )
        f.write(
            f"Average tokens per description: {analysis_results['token_stats']['avg']:.2f}\n\n"
        )

        f.write("=== SENTENCE STATISTICS ===\n")
        f.write(
            f"Maximum sentences in a description: {analysis_results['sentence_stats']['max']}\n"
        )
        f.write(
            f"Minimum sentences in a description: {analysis_results['sentence_stats']['min']}\n"
        )
        f.write(
            f"Average sentences per description: {analysis_results['sentence_stats']['avg']:.2f}\n"
        )
        f.write(
            f"Average words per sentence: {analysis_results['sentence_stats']['avg_words_per_sentence']:.2f}\n\n"
        )

        f.write("=== CLASS DISTRIBUTION ===\n")
        for label, count in sorted(
            analysis_results["class_counts"].items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (count / analysis_results["num_examples"]) * 100
            f.write(f"{label[6:]}: {count} examples ({percentage:.2f}%)\n")

        f.write("\n=== TOP LABEL COMBINATIONS ===\n")
        for combo, count in analysis_results["top_combinations"].items():
            percentage = (count / analysis_results["num_examples"]) * 100
            f.write(f"{combo}: {count} examples ({percentage:.2f}%)\n")

        # Additional histogram data
        token_bins = [0, 10, 20, 30, 40, 50, 75, 100, float("inf")]
        token_hist = {}

        # Recalculate token distribution for the histogram
        df = pd.read_csv(csv_file)
        descriptions = df["description"].astype(str)
        description_tokens = [word_tokenize(desc.lower()) for desc in descriptions]
        token_lengths = [len(tokens) for tokens in description_tokens]

        for i in range(len(token_bins) - 1):
            lower = token_bins[i]
            upper = token_bins[i + 1]
            count = sum(1 for length in token_lengths if lower <= length < upper)
            if upper == float("inf"):
                token_hist[f"{lower}+"] = count
            else:
                token_hist[f"{lower}-{upper-1}"] = count

        f.write("\n=== TOKEN LENGTH DISTRIBUTION ===\n")
        for bin_range, count in token_hist.items():
            percentage = (count / analysis_results["num_examples"]) * 100
            f.write(f"{bin_range} tokens: {count} examples ({percentage:.2f}%)\n")


if __name__ == "__main__":
    # Set the input and output file paths
    input_file = (
        "preference_dataset.csv"  # Change this if your file has a different name
    )
    output_file = "preference_dataset_analysis.txt"

    # Analyze the dataset
    try:
        results = analyze_dataset(input_file)
        write_analysis_to_file(results, output_file,input_file)
        print(f"Analysis complete! Results written to {output_file}")
    except Exception as e:
        print(f"Error: {e}")
        print("Please make sure the CSV file exists and has the correct format.")
