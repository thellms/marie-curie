# pdf_utils.py

import pandas as pd
import logging

logging.basicConfig(
    filename="research_helper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s",
)

def unify_pdf_urls(df: pd.DataFrame) -> list:
    """
    Extract URLs for PDFs from either:
      - 'openAccessPdf' (if it's a dict with {'url': ...})
      - 'url' (common fallback from other integrations like Litmaps or Crossref)

    Return a deduplicated list of valid PDF URLs.
    """
    pdf_urls = []

    # If 'openAccessPdf' from Semantic Scholar
    if "openAccessPdf" in df.columns:
        def _extract_s2_url(x):
            if isinstance(x, dict):
                return x.get("url")
            return None
        s2_urls = df["openAccessPdf"].apply(_extract_s2_url).dropna().tolist()
        pdf_urls.extend(s2_urls)

    # If 'url' from e.g. Litmaps or Crossref
    if "url" in df.columns:
        fallback_urls = df["url"].dropna().tolist()
        pdf_urls.extend(fallback_urls)

    # Remove duplicates, remove empty
    pdf_urls = set(u for u in pdf_urls if u and u.strip())
    return list(pdf_urls)
