# search.py

import asyncio
import logging
import requests
import json
import pandas as pd
import os
import time
import pathlib
import sqlite3
from datetime import datetime
import io
from paper_identifier import unify_doi 

from download_pdfs import download_pdfs
from grader import grade_paper
from parse import parse_pdfs_in_directory
from litmaps import search_litmaps
from db_manager import create_database, store_paper_data, store_query_data, get_existing_dois

import absl.logging
absl.logging.set_verbosity(absl.logging.ERROR)

logging.basicConfig(
    filename="research_helper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s",
)

# ---------------------------------------------------------------------------
# Utility: Make a GET request with retry and rate-limiting
# ---------------------------------------------------------------------------
def get_with_retry(url, max_retries=3, base_delay=2):
    """
    GET a URL with up to `max_retries` on certain errors (429, 500, 502, 503, 504).
    Uses exponential backoff, starting at `base_delay` seconds.
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response

        except requests.exceptions.HTTPError as e:
            status_code = response.status_code if response else None
            # Retry for certain status codes
            if status_code in [429, 500, 502, 503, 504] and attempt < max_retries:
                delay = base_delay * (2 ** (attempt - 1))  # exponential backoff
                logging.warning(f"Got HTTP {status_code} from S2. Retrying in {delay}s (attempt {attempt}/{max_retries})")
                time.sleep(delay)
                continue
            else:
                # Raise if we can't or won't retry
                raise

        except Exception as e:
            # Non-HTTP errors (network issues, etc.)
            if attempt < max_retries:
                delay = base_delay * (2 ** (attempt - 1))
                logging.warning(f"Error {e} from S2. Retrying in {delay}s (attempt {attempt}/{max_retries})")
                time.sleep(delay)
                continue
            else:
                raise


def search_and_save(query: str, fields: str, filepath: str):
    """
    After retrieving each paper from the API, we unify the DOI before
    writing the JSON lines. That ensures stable IDs for re-runs.
    """
    try:
        logging.debug(f"Starting search_and_save for query: {query}")
        base_url = "http://api.semanticscholar.org/graph/v1/paper/search/bulk"
        url = f"{base_url}?query={query}&fields={fields}"

        response = get_with_retry(url, max_retries=3, base_delay=2)
        r = response.json()

        total_estimated = r.get("total", "unknown")
        logging.info(f"Estimated documents for query '{query}': {total_estimated}")

        retrieved = 0
        with open(filepath, "a", encoding="utf-8") as file:
            while True:
                if "data" in r:
                    data = r["data"]
                    retrieved += len(data)
                    logging.debug(f"Retrieved {retrieved} papers for query '{query}' so far...")
                    for paper in data:
                        # Ensure a stable 'DOI' field
                        paper["DOI"] = unify_doi(paper)
                        # Write to file
                        file.write(json.dumps(paper) + "\n")

                if "token" not in r:
                    # No more pages
                    break

                token = r["token"]
                time.sleep(1)
                next_url = f"{url}&token={token}"
                response = get_with_retry(next_url, max_retries=3, base_delay=2)
                r = response.json()

        logging.info(f"Retrieved {retrieved} papers total for query: {query}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error searching for query '{query}': {e}")
    except Exception as e:
        logging.exception(f"An unexpected error occurred while searching for query '{query}'")


def extrude_external_ids(df: pd.DataFrame) -> pd.DataFrame:
    """
    Splits out the content of 'externalIds' column into separate columns, if present.
    """
    try:
        if "externalIds" not in df.columns:
            return df
        external_ids_df = df["externalIds"].apply(pd.Series)
        return pd.concat([df, external_ids_df], axis=1).drop(columns=["externalIds"])
    except Exception as e:
        logging.exception("An unexpected error occurred while extruding external IDs")
        raise


def extract_urls(df: pd.DataFrame) -> list:
    """
    Extracts all URLs from the 'openAccessPdf' column in a DataFrame.
    """
    try:
        if "openAccessPdf" not in df.columns:
            return []
        return df["openAccessPdf"].apply(
            lambda x: x.get("url") if isinstance(x, dict) else None
        ).tolist()
    except Exception as e:
        logging.exception("An unexpected error occurred while extracting URLs")
        raise


async def process_query(query: str, fields: str, output_dir: str) -> pd.DataFrame:
    """
    Asynchronously processes a single query: calls search_and_save() in a thread, then loads the JSONL as a DataFrame.
    """
    filename = query.lower().replace(" ", "_") + ".jsonl"
    filepath = os.path.join(output_dir, filename)

    await asyncio.to_thread(search_and_save, query, fields, filepath)

    if not os.path.exists(filepath):
        logging.warning(f"No data file created for query '{query}', returning empty DataFrame.")
        return pd.DataFrame()

    df = pd.read_json(filepath, lines=True)
    return df


async def process_and_download(user_query: str, queries: list, output_filename="merged_results.pkl"):
    """
    Processes multiple sub-queries asynchronously, merges results, downloads PDFs,
    parses them, and stores data in SQLite.
    """

    try:
        # fields to retrieve from the API
        fields = "title,year,abstract,externalIds,url,isOpenAccess,openAccessPdf,fieldsOfStudy"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join("query_jsons", timestamp)
        os.makedirs(output_dir, exist_ok=True)

        # 1) Create the database if it doesn't exist
        create_database()

        conn = sqlite3.connect("research_papers.db")

        try:
            # 2) Process all sub-queries in parallel
            tasks = [process_query(q, fields, output_dir) for q in queries]
            results = await asyncio.gather(*tasks)

            # 3) Merge all results
            merged_df = pd.concat(results, axis=0, ignore_index=True)

            # 4) Convert any "externalIds" -> top-level columns
            merged_df = extrude_external_ids(merged_df)

            # 5) Some papers might have their DOIs in merged_df["DOI"], or might be missing
            #    or might be in e.g. merged_df["DOI_x"]. Check if needed.

            # 6) Grade the papers
            logging.info("Grading papers for relevance...")

            def apply_grading(row):
                # row should have "abstract" and possibly a top-level "DOI"
                # If "DOI" not there, fallback (tempdoi) done in grader or earlier
                return grade_paper(user_query, row.get("abstract", ""), row.get("DOI", ""))

            merged_df["relevance_grade"] = merged_df.apply(apply_grading, axis=1)
            logging.info("Finished grading papers.")

            # 7) Filter for relevant papers
            relevant_df = merged_df[merged_df["relevance_grade"] == True].copy()

            # 8) Save the merged DataFrame
            relevant_df.to_pickle(output_filename)
            logging.info(f"Merged DataFrame of relevant papers saved to {output_filename}")

            # 9) Store data in SQLite
            store_paper_data(relevant_df.to_dict("records"))
            store_query_data(user_query, queries)

            # 10) Retrieve existing DOIs
            existing_dois = get_existing_dois()
            conn.commit()

            # 11) Filter out any that are missing abstracts or that are already in DB
            relevant_df = relevant_df[relevant_df["abstract"].notnull()]
            relevant_df = relevant_df[~relevant_df["DOI"].isin(existing_dois)]

            # 12) Filter for open access only
            if "isOpenAccess" in relevant_df.columns:
                relevant_df = relevant_df[relevant_df["isOpenAccess"] == True]

            if "openAccessPdf" not in relevant_df.columns:
                logging.warning("No 'openAccessPdf' column. Skipping PDF downloads.")
                return

            # 13) Extract URLs for PDFs
            urls = extract_urls(relevant_df)
            urls = [u for u in urls if u is not None]

            # 14) Download PDFs
            await asyncio.to_thread(download_pdfs, urls, "pdfs", relevant_df)

            # 15) Parse them
            await asyncio.to_thread(parse_pdfs_in_directory)

        finally:
            conn.close()

    except Exception as e:
        logging.exception("An unexpected error occurred while processing and downloading")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        logging.info("Usage: python search.py <query> [output_filename]")
        sys.exit(1)

    user_query = sys.argv[1]
    output_filename = sys.argv[2] if len(sys.argv) > 2 else "merged_results.pkl"

    logging.info("Starting search process...")

    from queries import query_chain
    results = query_chain.invoke({"query": user_query})

    async def main():
        await process_and_download(
            user_query=user_query,
            queries=results.queries,  # sub-queries from your LLM
            output_filename=output_filename,
        )

    asyncio.run(main())
