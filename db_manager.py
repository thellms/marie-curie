import logging
import os
import sqlite3
from datetime import datetime

# Configure logging
logging.basicConfig(filename='research_helper.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s')

def create_database():
    """
    Creates the SQLite database and tables if they don't exist.
    """
    try:
        conn = sqlite3.connect("research_papers.db")
        cursor = conn.cursor()

        # Create the papers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS papers (
                doi TEXT PRIMARY KEY,
                title TEXT,
                authors TEXT,
                year INTEGER,
                abstract TEXT,
                url TEXT,
                is_open_access BOOLEAN,
                pdf_url TEXT,
                relevance_grade BOOLEAN
            )
        ''')

        # Create the queries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                original_query TEXT,
                sub_queries TEXT
            )
        ''')

        conn.commit()
        conn.close()
        logging.info("SQLite database and tables created successfully.")
    except Exception as e:
        logging.exception(f"Error creating SQLite database: {e}")

def store_paper_data(paper_data):
    """
    Stores paper data in the SQLite database.

    Args:
      paper_data: A list of dictionaries, where each dictionary contains the data for a paper.
    """
    try:
        conn = sqlite3.connect("research_papers.db")
        cursor = conn.cursor()

        for paper in paper_data:
            cursor.execute('''
                INSERT OR IGNORE INTO papers (doi, title, authors, year, abstract, url, is_open_access, pdf_url, relevance_grade)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                paper.get('DOI'),
                paper.get('title'),
                ", ".join(paper.get('authors',)),
                paper.get('year'),
                paper.get('abstract'),
                paper.get('url'),
                paper.get('isOpenAccess'),
                paper.get('openAccessPdf', {}).get('url'),
                paper.get('relevance_grade')
            ))

        conn.commit()
        conn.close()
        logging.info("Paper data stored in SQLite database successfully.")
    except Exception as e:
        logging.exception(f"Error storing paper data in SQLite database: {e}")

def store_query_data(original_query, sub_queries):
    """
    Stores query data in the SQLite database.

    Args:
      original_query: The original user query.
      sub_queries: A list of sub-queries.
    """
    try:
        conn = sqlite3.connect("research_papers.db")
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO queries (timestamp, original_query, sub_queries)
            VALUES (?, ?, ?)
        ''', (datetime.now().isoformat(), original_query, ", ".join(sub_queries)))

        conn.commit()
        conn.close()
        logging.info("Query data stored in SQLite database successfully.")
    except Exception as e:
        logging.exception(f"Error storing query data in SQLite database: {e}")

def get_existing_dois():
    """
    Retrieves a set of existing DOIs from the database.

    Returns:
      A set of DOIs.
    """
    try:
        conn = sqlite3.connect("research_papers.db")
        cursor = conn.cursor()

        existing_dois = set()
        cursor.execute("SELECT doi FROM papers")
        for row in cursor.fetchall():
            existing_dois.add(row[0])

        conn.close()
        return existing_dois
    except Exception as e:
        logging.exception(f"Error retrieving existing DOIs from database: {e}")
        return set()  # Return an empty set in case of error