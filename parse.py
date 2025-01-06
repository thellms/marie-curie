### https://github.com/CatchTheTornado/pdf-extract-api

import logging
import os
import json
import unstructured_client
from unstructured_client.models import operations, shared
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# Configure logging
logging.basicConfig(filename='research_helper.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s')

def parse_pdf(filepath):
    try:
        client = unstructured_client.UnstructuredClient(
            api_key_auth=os.getenv("UNSTRUCTURED_API_KEY"),
            server_url="https://api.unstructuredapp.io",
        )

        with open(filepath, "rb") as f:
            data = f.read()

        req = operations.PartitionRequest(
            partition_parameters=shared.PartitionParameters(
                files=shared.Files(
                    content=data,
                    file_name=filepath,
                ),
                strategy=shared.Strategy.HI_RES,
                languages=['eng'],
            ),
        )

        res = client.general.partition(request=req)
        elements = res.elements  # Instead of res.partition_result.elements
        full_text = "\n".join(el.get("text", "").strip() for el in elements if el.get("text"))

        return elements, full_text

    except Exception as e:
        logging.error(f"Error parsing PDF {filepath}: {e}")
        return None, None


def save_parsed_content(filepath, elements, full_text):
    """
    Saves both parsed elements and a concatenated full text for the given PDF.
    """
    try:
        output_dir = "parsed_pdfs"
        os.makedirs(output_dir, exist_ok=True)

        base_name = os.path.splitext(os.path.basename(filepath))[0]

        # 1) JSONL for the structured elements
        elements_filename = base_name + "_elements.jsonl"
        elements_filepath = os.path.join(output_dir, elements_filename)

        with open(elements_filepath, "w", encoding="utf-8") as f:
            for el in elements:
                json_line = json.dumps(el, ensure_ascii=False)
                f.write(json_line + "\n")

        # 2) Plain text if you want
        text_filename = base_name + "_fulltext.txt"
        text_filepath = os.path.join(output_dir, text_filename)
        with open(text_filepath, "w", encoding="utf-8") as f:
            f.write(full_text)

        logging.info(f"Saved elements to {elements_filepath} and text to {text_filepath}")

    except Exception as e:
        logging.error(f"Error saving parsed content for {filepath}: {e}")


def parse_pdfs_in_directory(directory="pdfs"):
    """
    Parses all PDF files in a given directory, handling API limits.
    """
    parsed_count = 0
    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            filepath = os.path.join(directory, filename)

            # Check if parsed file already exists
            output_dir = "parsed_pdfs"
            base_name = os.path.splitext(os.path.basename(filepath))[0]
            # We'll say if we already have "_elements.jsonl", we skip
            elements_filename = base_name + "_elements.jsonl"
            elements_filepath = os.path.join(output_dir, elements_filename)

            if os.path.exists(elements_filepath):
                logging.info(f"Skipping already parsed file: {filename}")
                continue

            elements, full_text = parse_pdf(filepath)
            if elements is not None and full_text is not None:
                save_parsed_content(filepath, elements, full_text)
                parsed_count += 1

                # Check for API limit
                if parsed_count >= 1000:  # Adjust the limit as needed
                    logging.warning("Reached API limit for parsing. Resuming later.")
                    break

if __name__ == "__main__":
    parse_pdfs_in_directory()
