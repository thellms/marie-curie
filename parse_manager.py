# parse_manager.py

import os
import logging
import glob

from parse_unstructured import parse_pdf_unstructured, already_parsed_unstructured
from parse_pymupdf import parse_pdf_pymupdf, already_parsed_pymupdf

logging.basicConfig(
    filename='research_helper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s'
)

def parse_pdfs_in_directory(parser_method: str, directory="pdfs"):
    """
    Orchestrates PDF parsing with the chosen parser method.
    If parser_method == 'unstructured', we do parse_unstructured.
    If parser_method == 'pymupdf', we do parse_pymupdf.
    """
    parsed_count = 0
    pdf_files = glob.glob(os.path.join(directory, "*.pdf"))
    for filepath in pdf_files:
        if parser_method.lower() == "pymupdf":
            if already_parsed_pymupdf(filepath):
                logging.info(f"Skipping parse for {filepath}, pymupdf output exists.")
                continue
            parse_pdf_pymupdf(filepath)
            parsed_count += 1

        else:
            # default unstructured
            if already_parsed_unstructured(filepath):
                logging.info(f"Skipping parse for {filepath}, unstructured output exists.")
                continue
            parse_pdf_unstructured(filepath)
            parsed_count += 1

    logging.info(f"Done parsing {parsed_count} new PDF(s) with method '{parser_method}'")


