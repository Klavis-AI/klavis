import os
from typing import List, Optional

from scholarly import scholarly

MAX_RESULTS = 10


def _get_proxy_url() -> Optional[str]:
    """Build proxy URL from environment variables (same as duckduckgo server)."""
    username = os.environ.get("PROXY_USERNAME")
    password = os.environ.get("PROXY_PASSWORD")
    if not (username and password):
        return None
    host = os.environ.get("PROXY_HOST", "p.webshare.io")
    scheme = os.environ.get("PROXY_SCHEME", "http")
    port = os.environ.get("PROXY_PORT", "1080" if "socks" in scheme else "80")
    return f"{scheme}://{username}:{password}@{host}:{port}"


class GoogleScholar:
    def __init__(self):
        self.scholarly = scholarly
        proxy = _get_proxy_url()
        if proxy:
            self.scholarly.use_proxy(http=proxy, https=proxy)

    def get_scholarly(self, keyword):
        return self.scholarly.search_pubs(keyword)

    @staticmethod
    def _parse_results(search_results):
        articles = []
        results_iter = 0
        for searched_article in search_results:
            bib = searched_article.get('bib', {})
            title = bib.get('title', 'No title')
            authors = bib.get('author', [])
            if isinstance(authors, list):
                authors = ", ".join(authors)
            elif authors is None:
                authors = "No authors available"
            
            pub_year = bib.get('pub_year', 'No year available')
            venue = bib.get('venue', 'No venue available')
            abstract = bib.get('abstract', 'No abstract available')
            
            pub_url = searched_article.get('pub_url', 'No URL available')
            num_citations = searched_article.get('num_citations', 'No citation count')
            citedby_url = searched_article.get('citedby_url', 'No cited-by URL')
            url_related_articles = searched_article.get('url_related_articles', 'No related articles URL')
            gsrank = searched_article.get('gsrank', 'No ranking available')
            author_id = searched_article.get('author_id', [])
            if isinstance(author_id, list):
                author_id = ", ".join(author_id) if author_id else "No author IDs"
            
            article_string = "\n".join([
                f"Title: {title}",
                f"Authors: {authors}",
                f"Publication Year: {pub_year}",
                f"Venue: {venue}",
                f"Google Scholar Rank: {gsrank}",
                f"Citations: {num_citations}",
                f"Author IDs: {author_id}",
                f"Publication URL: {pub_url}",
                f"Cited-by URL: {citedby_url}",
                f"Related Articles URL: {url_related_articles}",
                f"Abstract: {abstract}",
            ])
            
            articles.append(article_string)
            results_iter += 1
            if results_iter >= MAX_RESULTS:
                break
        return articles

    def search_pubs(self, keyword) -> List[str]:
        search_results = self.scholarly.search_pubs(keyword)
        articles = self._parse_results(search_results)
        return articles
