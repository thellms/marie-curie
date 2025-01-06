# semantic_scholar_integration.py

import requests
import logging
from typing import List, Dict
from aggregator_utils import unify_pdf_urls  # optional if we want to unify URL extraction here

logging.basicConfig(...)

API_BASE_URL = "http://api.semanticscholar.org/graph/v1/paper/search"

def search_semantic_scholar_api(query: str, fields: str = "title,year,abstract,externalIds,url,isOpenAccess,openAccessPdf,fieldsOfStudy") -> List[Dict]:
    """
    Returns a list of dicts, each representing a paper from semantic scholar, unifying basic fields:
      {
        "title": str,
        "abstract": str,
        "year": int or None,
        "DOI": str or None,
        "authors": [...],  # optional
        "isOpenAccess": bool,
        "openAccessPdf": { "url": ... } or None,
        ...
      }

    We'll do pagination if needed. 
    For simplicity, we do single pass or partial pagination. 
    """
    # We do simpler approach than the old "bulk" endpoint, or we can do the same
    # We'll do a single request for now:
    # If you still want the /bulk endpoint, adapt accordingly.

    # We'll do the simpler /graph/v1/paper/search?query=...
    # or the old "bulk" method. This code is just an example.
    # If you prefer your old "bulk" + token approach, replicate it.

    url = f"{API_BASE_URL}"
    params = {
        "query": query,
        "fields": fields,
        "limit": 100,
    }
    all_papers = []
    try:
        r = requests.get(url, params=params, timeout=30)
        if r.status_code != 200:
            logging.error(f"Semantic Scholar API error: {r.status_code} for query={query}")
            return []

        data = r.json()
        items = data.get("data", [])
        for paper in items:
            # unify minimal fields
            title = paper.get("title", "")
            abstract = paper.get("abstract", "")
            year = paper.get("year")
            is_open_access = paper.get("isOpenAccess", False)
            open_access_pdf = paper.get("openAccessPdf", None)

            # externalIds might contain "DOI"
            external_ids = paper.get("externalIds", {})
            doi = external_ids.get("DOI") if external_ids else None

            paper_dict = {
                "title": title,
                "abstract": abstract,
                "year": year,
                "DOI": doi,
                "isOpenAccess": is_open_access,
                "openAccessPdf": open_access_pdf,
            }
            all_papers.append(paper_dict)

        return all_papers

    except Exception as e:
        logging.exception(f"Error searching S2 for query '{query}': {e}")
        return []
