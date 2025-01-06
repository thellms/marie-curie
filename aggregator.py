# aggregator.py

import os
import sys
import argparse
import logging
import asyncio
import sqlite3
from datetime import datetime

import pandas as pd

from queries import query_chain
from db_manager import create_database, store_paper_data, store_query_data, get_existing_dois
from grader import grade_paper
from download_pdfs import download_pdfs
from parse_manager import parse_pdfs_in_directory
from aggregator_utils import aggregate_subquery_results, unify_final_df
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

logging.basicConfig(
    filename="research_helper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s",
)

async def run_pipeline(user_query: str, parser_method: str, output_filename: str = "merged_results.pkl"):
    """
    High-level pipeline:
      1) Decompose query into sub-queries
      2) For each sub-query, gather data from multiple sources
      3) Merge & unify results
      4) Grade (LLM), store in DB, skip duplicates
      5) Download + parse PDFs using the chosen parser method
    """
    # 1) Decompose the user query
    results = query_chain.invoke({"query": user_query})
    sub_queries = results.queries  # a list of sub-queries

    # 2) Create DB if needed
    create_database()
    conn = sqlite3.connect("research_papers.db")

    try:
        # 3) aggregator logic for each sub-query
        tasks = [aggregate_subquery_results(q) for q in sub_queries]
        dfs = await asyncio.gather(*tasks)
        merged_df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

        # 4) LLM grade
        logging.info("Grading papers for relevance...")

        def apply_grading(row):
            return grade_paper(user_query, row.get("abstract", ""), row.get("DOI", ""))

        merged_df["relevance_grade"] = merged_df.apply(apply_grading, axis=1)

        # Filter relevant
        relevant_df = merged_df[merged_df["relevance_grade"] == True].copy()
        relevant_df.to_pickle(output_filename)
        logging.info(f"Saved relevant merged DF to {output_filename}")

        # 5) Store in DB
        store_paper_data(relevant_df.to_dict("records"))
        store_query_data(user_query, sub_queries)

        existing_dois = get_existing_dois()
        conn.commit()

        # Filter out existing or missing abstracts
        relevant_df = relevant_df[relevant_df["abstract"].notnull()]
        relevant_df = relevant_df[~relevant_df["DOI"].isin(existing_dois)]

        # 6) Download PDFs
        #   We'll guess if the data has "isOpenAccess" from semantic scholar. 
        #   For litmaps, we might not have that col. We'll skip that check or do a fallback.
        if "isOpenAccess" in relevant_df.columns:
            relevant_df = relevant_df[relevant_df["isOpenAccess"] == True]

        # For semantic scholar, we might have 'openAccessPdf' col. For litmaps, we might have 'url'.
        # We'll unify these in aggregator_utils if needed. For now, let's just check both.
        # We'll define a function unify_pdf_urls below if we want.
        from aggregator_utils import unify_pdf_urls
        pdf_urls = unify_pdf_urls(relevant_df)

        await asyncio.to_thread(download_pdfs, pdf_urls, "pdfs", relevant_df)

        # 7) Parse with the chosen parser method
        #   parse_pdfs_in_directory can be told which method to use
        await asyncio.to_thread(parse_pdfs_in_directory, parser_method, "pdfs")

    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Aggregator pipeline with multiple APIs and parser methods.")
    parser.add_argument("query", type=str, help="User's research query")
    parser.add_argument("--parser", type=str, default="unstructured",
                        help="Which parser method to use. Options: 'unstructured' or 'pymupdf'")
    parser.add_argument("--output", type=str, default="merged_results.pkl",
                        help="Output file for the final relevant DataFrame")

    args = parser.parse_args()

    user_query = args.query
    parser_method = args.parser
    output_filename = args.output

    logging.info("Starting aggregator pipeline...")

    asyncio.run(run_pipeline(user_query, parser_method, output_filename))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logging.info("Usage: python aggregator.py 'query' [--parser=...] [--output=...]")
        sys.exit(1)

    main()
