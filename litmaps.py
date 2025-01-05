# litmaps_integration.py

import requests
import logging
from typing import List, Dict

logging.basicConfig(
    filename="research_helper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s",
)

LITMAPS_BASE_URL = "https://api.litmaps.com/keywordSearch"

def search_litmaps(
    query: str,
    use_reranker: bool = False,
    page: int = 1,
    per: int = 100,
) -> List[Dict]:
    """
    Searches Litmaps for a given query. Returns a list of dicts in a consistent format:
      {
        "title": str,
        "abstract": str,
        "authors": [str, ...],
        "year": int or None,
        "DOI": str or None,
        "url": str or None,
        ... plus other fields
      }

    Args:
      query (str): The user query or sub-query
      use_reranker (bool): Whether to set "useReranker" param
      page (int): page number
      per (int): results per page

    Returns:
      List[dict]: a list of paper data in the standardized schema.
    """
    params = {
        "query": query,
        "useReranker": use_reranker,
        "showArticleDetails": True,
        "page": page,
        "per": per,
    }

    papers = []
    try:
        response = requests.get(LITMAPS_BASE_URL, params=params)
        if response.status_code != 200:
            logging.error(f"Litmaps API error {response.status_code} for query={query}")
            return []

        data = response.json()
        result_items = data.get("resultItems", [])
        for article in result_items:
            # We'll unify fields
            title = article.get("title", "")
            author_string = article.get("authorString", "")
            # Convert to a list of authors
            authors = [a.strip() for a in author_string.split(",")] if author_string else []
            publication_date = article.get("publicationDate")
            # We'll try to parse year from publicationDate
            year = None
            if publication_date and len(publication_date) >= 4:
                # e.g. "2023-05-31T00:00:00Z" => year=2023
                try:
                    year = int(publication_date[:4])
                except:
                    year = None

            doi = article.get("doi", "").strip() or None
            url = article.get("url", "").strip() or None

            # If abstract is not found, store entire object or None
            abstract = article.get("abstract")
            if not abstract:
                abstract = ""  # or store str(article)

            # For additional fields, we can store them in custom fields or ignore
            # We'll keep "publication_title" in a custom field
            publication_title = article.get("publicationTitle", "")
            # forward/backward edges might not be relevant to the final aggregator schema, but we can store if we want
            forward_edge_count = article.get("forward_edge_count", 0)
            backward_edge_count = article.get("backward_edge_count", 0)

            paper_dict = {
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "year": year,
                "DOI": doi,
                "url": url,
                # If you want to unify with the semantic scholar style "isOpenAccess", you can do so, 
                # but we don't have that data here. We'll store some extras as well:
                "publication_title": publication_title,
                "forward_edge_count": forward_edge_count,
                "backward_edge_count": backward_edge_count,
            }

            papers.append(paper_dict)

        return papers

    except Exception as e:
        logging.exception(f"Error searching Litmaps for query={query}: {e}")
        return []
