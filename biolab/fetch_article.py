import requests


def fetch_article(pubmed_id):
    url = f"https://pubmed.ncbi.nlm.nih.gov/{pubmed_id}/"
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Failed to fetch article with ID {pubmed_id}")
