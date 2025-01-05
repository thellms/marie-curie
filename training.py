import json
import logging
import os

def prepare_training_data(log_dir="llm_logs"):
    """
    Extracts data from LLM call logs and prepares it for fine-tuning.

    Args:
      log_dir: The directory containing the LLM call log files.

    Returns:
      A list of dictionaries, where each dictionary represents a training example.
    """
    training_data = []
    for filename in os.listdir(log_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(log_dir, filename)
            try:
                with open(filepath, "r") as f:
                    log_entry = json.load(f)

                # Extract relevant information for fine-tuning
                user_query = log_entry["user_query"]
                abstract = log_entry["abstract"]
                response = log_entry["response"]
                doi = log_entry.get("doi")

                # Create a training example
                training_example = {
                    "user_query": user_query,
                    "abstract": abstract,
                    "completion": response,  # Use "completion" as the key for many LLMs
                    "doi": doi,
                }
                training_data.append(training_example)

            except Exception as e:
                logging.error(f"Error processing log file {filename}: {e}")

    return training_data

def main():
    """
    Main function to extract and save the training data.
    """
    training_data = prepare_training_data()

    # Save the training data in a suitable format (e.g., JSONL)
    with open("training_data.jsonl", "w") as f:
        for example in training_data:
            print(json.dumps(example), file=f)

if __name__ == "__main__":
    main()