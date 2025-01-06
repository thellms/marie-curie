# crossref_integration.py

import requests
import logging
from typing import List, Dict
import time

logging.basicConfig(
    filename="research_helper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s",
)

BASE_URL = "https://api.crossref.org/works"


def search_crossref(
    query: str,
    has_abstract: bool = True,
    rows: int = 100,
    mailto: str = "adrian.s.delasierra@gmail.com",
    max_pages: int = 5,
) -> List[Dict]:
    """
    Searches Crossref for the given query. Retrieves up to `rows * max_pages` items (with a cursor approach).
    Normalizes the results into a consistent format.

    Args:
      query (str): The search query
      has_abstract (bool): Whether to filter results to only those with abstracts
      rows (int): The number of items to retrieve per page
      mailto (str): The contact email to pass to Crossref
      max_pages (int): Maximum number of pages/cursors to fetch (avoid infinite loops)

    Returns:
      List[Dict]: A list of dicts, each representing one paper in a consistent schema:
        {
          "title": str,
          "abstract": str,
          "year": Optional[int],
          "DOI": Optional[str],
          "authors": List[str],
          "url": Optional[str],
          ... any other fields
        }
    """

    # Build initial query parameters
    params = {
        "query": query,
        "rows": rows,
        "mailto": mailto,
        "cursor": "*",  # start
    }

    # Optionally filter has-abstract
    # Crossref docs: e.g. "filter": "has-abstract:true"
    if has_abstract:
        params["filter"] = "has-abstract:true"

    all_results = []
    pages_fetched = 0

    while True:
        response = requests.get(BASE_URL, params=params)
        if response.status_code != 200:
            logging.error(f"Crossref API error: {response.status_code}, {response.text}")
            break

        data = response.json()
        items = data.get("message", {}).get("items", [])
        all_results.extend(items)

        next_cursor = data.get("message", {}).get("next-cursor")
        if not next_cursor or len(items) == 0:
            # No more pages
            break

        pages_fetched += 1
        if pages_fetched >= max_pages:
            logging.info(f"Reached max_pages={max_pages}, stopping Crossref fetch.")
            break

        # Set the cursor for the next request
        params["cursor"] = next_cursor

        # Basic sleep to be nice to Crossref
        time.sleep(1)

    logging.info(f"Crossref search '{query}': retrieved {len(all_results)} items in {pages_fetched} pages.")

    # Now let's unify them in a consistent schema
    normalized = []
    for item in all_results:
        # Title
        titles = item.get("title", [])
        title = titles[0] if titles else ""

        # Abstract (Crossref often has them in HTML tags, might need cleaning)
        abstract = item.get("abstract", "")
        # Possibly strip HTML if needed
        abstract = _strip_html_tags(abstract)

        # Year (from 'published-print' or 'published-online' or 'created' date-parts)
        year = None
        pub_date = item.get("published-print") or item.get("published-online") or item.get("created")
        if pub_date:
            date_parts = pub_date.get("date-parts", [])
            # e.g. [[2023, 5, 13]]
            if date_parts and isinstance(date_parts[0], list) and len(date_parts[0]) > 0:
                try:
                    year = int(date_parts[0][0])
                except:
                    year = None

        # Authors
        authors = []
        author_list = item.get("author", [])
        for a in author_list:
            # Format "LastName, FirstName"
            family = a.get("family", "")
            given = a.get("given", "")
            full = (family + ", " + given).strip(", ")
            authors.append(full)

        # DOI
        doi = item.get("DOI", "").strip()

        # URL
        url = item.get("URL", "").strip()

        # Construct normalized dict
        paper_dict = {
            "title": title,
            "abstract": abstract,
            "year": year,
            "DOI": doi,
            "authors": authors,
            "url": url,
        }

        normalized.append(paper_dict)

    return normalized


def _strip_html_tags(raw_html: str) -> str:
    """
    Quick helper to remove basic HTML tags from Crossref abstracts, if needed.
    It's not a robust HTML parser, but for simple usage it might suffice.
    """
    import re
    cleantext = re.sub(r"<.*?>", "", raw_html)
    return cleantext.strip()
