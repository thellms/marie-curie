# parse_pymupdf.py

import os
import logging
import pathlib
import pymupdf4llm

logging.basicConfig(
    filename='research_helper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s'
)

OUTPUT_DIR = "parsed_pdfs_pymupdf"

def already_parsed_pymupdf(pdf_path: str) -> bool:
    """
    Check if we already have a .md or .txt for this PDF in OUTPUT_DIR
    """
    base = os.path.splitext(os.path.basename(pdf_path))[0]
    md_path = os.path.join(OUTPUT_DIR, base + ".md")
    return os.path.exists(md_path)

def parse_pdf_pymupdf(pdf_path: str):
    """
    Using pymupdf4llm to parse PDF -> markdown text.
    """
    try:
        md_text = pymupdf4llm.to_markdown(pdf_path)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        base = os.path.splitext(os.path.basename(pdf_path))[0]
        out_path = os.path.join(OUTPUT_DIR, base + ".md")

        pathlib.Path(out_path).write_bytes(md_text.encode("utf-8"))
        logging.info(f"pymupdf parse complete for {pdf_path}, saved to {out_path}")
    except Exception as e:
        logging.error(f"Error parsing PDF {pdf_path} with pymupdf4llm: {e}")
