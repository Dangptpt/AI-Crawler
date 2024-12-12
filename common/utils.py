import re
import requests
from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup


def fetch_html(url):
    try:
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10
        )
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        response = session.get(url)
        response.raise_for_status()

        html_content = response.text
        soup = BeautifulSoup(html_content, 'lxml')

        for script in soup.find_all(['script', 'style', 'noscript']):
            script.decompose()

        cleaned_html = str(soup)
        return cleaned_html
    except requests.exceptions.RequestException as e:
        print(f"Fetch html failed: {e}")
        return None


def get_clean_text_from_html(text):
    # Parse HTML content
    soup = BeautifulSoup(text, 'html.parser')

    # Get the text with newline between tags
    cleaned_text = soup.get_text(separator="\n")

    # Remove excessive whitespace but preserve newlines
    cleaned_text = re.sub(r'\s*\n\s*', '\n', cleaned_text).strip()

    return cleaned_text
