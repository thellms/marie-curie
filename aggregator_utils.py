# aggregator_utils.py

import logging
import pandas as pd
from typing import List

from semantic_scholar import search_semantic_scholar_api
from litmaps import search_litmaps
from crossref import search_crossref
from paper_identifier import unify_doi

logging.basicConfig(
    filename="research_helper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s",
)

def aggregate_subquery_results(query: str) -> pd.DataFrame:
    """
    1) call Semantic Scholar
    2) call Litmaps
    3) call Crossref
    4) unify all results
    5) return single DataFrame
    """
    s2_results = search_semantic_scholar_api(query)
    for item in s2_results:
        item["DOI"] = unify_doi(item)
    s2_df = pd.DataFrame(s2_results)

    litmaps_results = search_litmaps(query=query, use_reranker=False, page=1, per=1000)
    for item in litmaps_results:
        item["DOI"] = unify_doi(item)
    litmaps_df = pd.DataFrame(litmaps_results)

    crossref_results = search_crossref(query=query, has_abstract=True, rows=100, max_pages=5)
    for item in crossref_results:
        item["DOI"] = unify_doi(item)
    crossref_df = pd.DataFrame(crossref_results)

    combined_df = pd.concat([s2_df, litmaps_df, crossref_df], ignore_index=True)
    logging.info(f"aggregate_subquery_results -> got {len(combined_df)} items for '{query}' across 3 APIs")
    return combined_df

def unify_final_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    If you had a separate function to do any final cleaning or dedup logic,
    you could keep it here. 
    If you don't need it, remove or adapt as needed.
    """
    # Example placeholder:
    # This could do additional dedup logic or title-based fuzzy matching
    return df
