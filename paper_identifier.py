import hashlib

def generate_stable_fallback_doi(paper_dict: dict) -> str:
    """
    Generates a stable fallback DOI (tempdoi-<HASH>) for a paper that has no real DOI.
    We want this to be deterministic, so re-processing the same paper yields the same fallback.
    
    We hash relevant fields (title, year, maybe authors, abstract) so that if we see
    the same paper again, we produce the same ID.

    Args:
        paper_dict: The dict containing paper metadata (title, year, abstract, authors, etc.)

    Returns:
        A string like: "tempdoi-349ab0dc12d5" (short hash)
    """
    title = (paper_dict.get("title") or "").strip().lower()
    year = str(paper_dict.get("year") or "").strip()
    abstract = (paper_dict.get("abstract") or "").strip().lower()
    authors = ""

    # If you want to incorporate authors in the hash, do so
    # authors_list = paper_dict.get("authors", [])  # e.g. a list
    # authors = " ".join(a.strip().lower() for a in authors_list)

    # Combine the strings
    raw_str = title + year + abstract + authors
    # Create a stable SHA1 or SHA256
    short_hash = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()[:12]
    return f"tempdoi-{short_hash}"


def unify_doi(paper_dict: dict) -> str:
    """
    Returns the final DOI for a paper. If the paper has a real 'DOI', we use that.
    Otherwise, we generate a stable fallback using `generate_stable_fallback_doi`.

    Args:
        paper_dict: The dict containing paper metadata.

    Returns:
        A string representing the final (real or fallback) DOI for the paper.
    """
    doi = paper_dict.get("DOI")
    if doi and isinstance(doi, str) and doi.strip():
        # We have a real DOI
        return doi.strip()
    # Else produce a stable fallback
    return generate_stable_fallback_doi(paper_dict)
