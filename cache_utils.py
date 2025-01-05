# cache_utils.py

import hashlib
import json
import logging
import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine

from langchain_community.cache import SQLAlchemyCache
from langchain_community.cache import FullLLMCache
from langchain.schema import Generation  # needed to store and retrieve from the cache

# Configure logging
logging.basicConfig(
    filename="research_helper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s",
)

# -------------------------------------------------------------------------
# Initialize the SQLAlchemyCache
#   According to your docs, we do:
#       .lookup(prompt: str, llm_string: str) -> Optional[List[Generation]]
#       .update(prompt: str, llm_string: str, return_val: List[Generation]) -> None
# -------------------------------------------------------------------------

engine = create_engine("sqlite:///research_helper.db")
cache = SQLAlchemyCache(engine=engine)
FullLLMCache.metadata.create_all(bind=engine)
# e.g.:
# from sqlalchemy import create_engine
# engine = create_engine("sqlite:///research_helper.db")
# cache = SQLAlchemyCache(engine=engine)

LLM_STRING = "paper-grader-v1"  # A constant identifying our "LLM config"

def _clean_doi(doi: str) -> str:
    """
    Returns a fallback "tempdoi-<UUID>" if the given doi is None, 'nan', or empty.
    Otherwise returns doi.strip().
    """
    if not doi or not isinstance(doi, str):
        return f"tempdoi-{uuid.uuid4()}"
    doi_str = doi.strip().lower()
    if doi_str == "nan":
        return f"tempdoi-{uuid.uuid4()}"
    return doi.strip()

# -------------------------------------------------------------------------
# Convert bool -> List[Generation(text=...)]
# -------------------------------------------------------------------------
def _bool_to_generations(is_relevant: bool) -> list[Generation]:
    text_value = "true" if is_relevant else "false"
    return [Generation(text=text_value)]

# -------------------------------------------------------------------------
# Convert List[Generation(text=...)] -> bool
# -------------------------------------------------------------------------
def _generations_to_bool(gens: list[Generation]) -> bool:
    if not gens:
        return False
    first_text = gens[0].text.strip().lower()
    return (first_text == "true")

# -------------------------------------------------------------------------
# Caching interface
# -------------------------------------------------------------------------
def get_cached_result(doi: str) -> bool | None:
    """
    Retrieves a boolean from the cache for the given DOI,
    or None if not found.

    Internally:
      .lookup(prompt=..., llm_string=LLM_STRING) -> Optional[List[Generation]]
    """
    try:
        safe_doi = _clean_doi(doi)
        prompt_str = f"doi:{safe_doi}"  # Single string
        result_list = cache.lookup(prompt_str, LLM_STRING)
        if result_list is None:
            return None

        return _generations_to_bool(result_list)

    except Exception as e:
        logging.error(f"Error retrieving cached result for DOI={doi}: {e}")
        return None

def store_result_in_cache(doi: str, is_relevant: bool):
    """
    Stores a bool in the cache as [Generation(text="true")] or [Generation(text="false")].
    """
    try:
        safe_doi = _clean_doi(doi)
        prompt_str = f"doi:{safe_doi}"
        gens = _bool_to_generations(is_relevant)  # e.g. [Generation(text="true")]
        cache.update(prompt_str, LLM_STRING, gens)

    except Exception as e:
        logging.error(f"Error storing result in cache for DOI={doi}: {e}")

# -------------------------------------------------------------------------
# LLM call logging
# -------------------------------------------------------------------------
def log_llm_call(user_query, abstract, response, model_name, doi=None):
    """
    Logs the LLM call and response to a JSON file in /llm_logs.
    """
    try:
        safe_query = user_query if user_query else ""
        safe_abstract = abstract if abstract else ""
        combined_text = safe_query + safe_abstract

        prompt_hash = hashlib.md5(combined_text.encode("utf-8")).hexdigest()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"llm_call_{timestamp}_{prompt_hash}.json"
        filepath = os.path.join("llm_logs", filename)

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model_name,
            "user_query": safe_query,
            "abstract": safe_abstract,
            "response": response,
            "doi": doi,
        }

        os.makedirs("llm_logs", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(log_entry, f, indent=4)

    except Exception as e:
        logging.error(f"Error logging LLM call: {e}")
