import streamlit as st
import sqlite3
import pandas as pd
import os

DATABASE_PATH = "research_papers.db"


def main():
    """
    Streamlit-based UI to display papers from 'research_papers.db' and allow
    basic text search in title/abstract.

    Steps:
      1) Connect to local SQLite
      2) Let user input a search term
      3) Query 'papers' table with LIKE filtering
      4) Display results in a modern interactive table
    """
    st.set_page_config(
        page_title="Marie Curie: Paper Viewer",
        layout="wide"
    )
    st.title("Marie Curie: Paper Viewer")

    # Check DB existence
    if not os.path.exists(DATABASE_PATH):
        st.error(f"Database file '{DATABASE_PATH}' not found. Make sure the aggregator pipeline ran.")
        return

    st.write("""
    This interface shows all papers stored in the local SQLite database, 
    with a simple search in the title or abstract fields. 
    """)

    # Search input
    search_term = st.text_input("Search (title/abstract)")

    # If empty search term, we show everything. If not, filter.
    if st.button("Search in Database"):
        results_df = fetch_papers(search_term)
        if results_df.empty:
            st.warning("No results found for that search.")
        else:
            st.success(f"Found {len(results_df)} papers.")
            # Display
            st.dataframe(results_df, use_container_width=True)
    else:
        # On first load, show everything
        results_df = fetch_papers("")
        st.info("Displaying all papers (use the search box to filter).")
        st.dataframe(results_df, use_container_width=True)


def fetch_papers(search_term: str) -> pd.DataFrame:
    """
    Connects to 'research_papers.db', selects relevant columns from the 'papers' table
    where the title OR abstract matches the search term. 
    Returns a DataFrame with columns [title, authors, abstract, year, doi].
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        # We'll search both title and abstract via LIKE
        # Searching authors is optional, you can add "authors LIKE :param" OR ...
        query = """
        SELECT 
            title,
            authors,
            abstract,
            year,
            doi
        FROM papers
        WHERE
            title LIKE :param
            OR abstract LIKE :param
        ORDER BY year DESC
        """
        param = f"%{search_term}%"
        rows = conn.execute(query, {"param": param}).fetchall()
        colnames = [desc[0] for desc in conn.execute(query, {"param": param}).description]
        results = [dict(zip(colnames, row)) for row in rows]
        df = pd.DataFrame(results)
        conn.close()

        # If 'authors' is stored as a string (like "Author1, Author2"), 
        # you might parse it into a list or keep as is. We'll keep as is for display.
        # Make year an integer if needed
        if not df.empty and "year" in df.columns:
            df["year"] = df["year"].fillna("").astype(str)

        return df
    except Exception as e:
        st.error(f"Error querying DB: {e}")
        return pd.DataFrame()


if __name__ == "__main__":
    main()
