import os
import requests
import logging

logging.basicConfig(filename='research_helper.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s')

def download_pdfs(urls, directory="pdfs", df=None):
    """
    If df is provided, we name the file based on the row's 'DOI' or 'title'.
    Then we skip if it already exists.
    """
    headers = {"User-Agent": "Mozilla/5.0 ..."}
    failed_urls = []

    if not os.path.exists(directory):
        os.makedirs(directory)

    for i, url in enumerate(urls):
        try:
            if df is not None:
                # We rely on the final stable 'DOI'
                doi = df["DOI"].iloc[i]
                safe_doi = "".join(c for c in doi if c.isalnum() or c in "._-").rstrip()[:100]
                filename = f"{safe_doi}.pdf"
            else:
                filename = os.path.basename(url)
                if not filename.endswith(".pdf"):
                    filename += ".pdf"

            filepath = os.path.join(directory, filename)
            if os.path.exists(filepath):
                logging.info(f"Skipping download, already exists: {filepath}")
                continue

            response = requests.get(url, stream=True, headers=headers)
            response.raise_for_status()

            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logging.info(f"Downloaded {filename} to {directory}")

        except requests.exceptions.RequestException as e:
            logging.error(f"Error downloading {url}: {e}")
            failed_urls.append(url)
        except Exception as e:
            logging.exception(f"Error downloading {url}")
            failed_urls.append(url)

    # If any failed
    if failed_urls:
        with open(os.path.join(directory, "failed_urls.txt"), "w") as f:
            for url in failed_urls:
                f.write(url + "\n")
        logging.info("List of failed URLs saved to failed_urls.txt")