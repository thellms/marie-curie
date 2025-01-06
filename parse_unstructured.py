# parse_unstructured.py

import logging
import os
import json
import unstructured_client
from unstructured_client.models import operations, shared
import pathlib

logging.basicConfig(
    filename='research_helper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s'
)

OUTPUT_DIR = "parsed_pdfs_unstructured"

def already_parsed_unstructured(pdf_path: str) -> bool:
    """
    Check if we already have a parsed file for this PDF in OUTPUT_DIR,
    for example <basename>_elements.jsonl or <basename>_fulltext.txt
    """
    base = os.path.splitext(os.path.basename(pdf_path))[0]
    jsonl_path = os.path.join(OUTPUT_DIR, base + "_elements.jsonl")
    return os.path.exists(jsonl_path)

def parse_pdf_unstructured(pdf_path: str):
    """
    Using unstructured approach.
    """
    try:
        client = unstructured_client.UnstructuredClient(
            api_key_auth=os.getenv("UNSTRUCTURED_API_KEY"),
            server_url="https://api.unstructuredapp.io",
        )

        with open(pdf_path, "rb") as f:
            data = f.read()

        req = operations.PartitionRequest(
            partition_parameters=shared.PartitionParameters(
                files=shared.Files(content=data, file_name=pdf_path),
                strategy=shared.Strategy.HI_RES,
                languages=['eng'],
            ),
        )

        res = client.general.partition(request=req)
        elements = res.elements
        full_text = "\n".join(el.get("text", "").strip() for el in elements if el.get("text"))

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        base = os.path.splitext(os.path.basename(pdf_path))[0]

        # Save elements as JSONL
        elements_path = os.path.join(OUTPUT_DIR, base + "_elements.jsonl")
        with open(elements_path, "w", encoding="utf-8") as f:
            for el in elements:
                f.write(json.dumps(el, ensure_ascii=False) + "\n")

        # Save full text
        text_path = os.path.join(OUTPUT_DIR, base + "_fulltext.txt")
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(full_text)

        logging.info(f"Unstructured parse complete for {pdf_path}, saved to {OUTPUT_DIR}")

    except Exception as e:
        logging.error(f"Error parsing PDF {pdf_path} with unstructured: {e}")
