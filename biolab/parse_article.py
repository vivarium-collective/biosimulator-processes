from bs4 import BeautifulSoup


def parse_article(article_html):
    soup = BeautifulSoup(article_html, 'html.parser')
    # Extract relevant sections from the article
    title = soup.find('h1', {'class': 'heading-title'}).get_text(strip=True)
    abstract = soup.find('div', {'class': 'abstract-content'}).get_text(strip=True)
    return {
        'title': title,
        'abstract': abstract
    }
