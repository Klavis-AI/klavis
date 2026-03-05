import arxiv
from typing import List

client = arxiv.Client()


class ArxivSearch:
    def __init__(self):
        self.client = arxiv.Client()

    def arxiv_search(self, keyword, max_results=10):
        search = arxiv.Search(query=keyword, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance)
        results = self.client.results(search)
        all_results = list(results)
        return all_results

    @staticmethod
    def _parse_results(results):
        formatted_results = []

        for result in results:
            title = result.title
            authors = ", ".join([str(author) for author in result.authors])
            summary = result.summary
            categories = ", ".join(result.categories)
            primary_category = result.primary_category
            published = result.published.strftime("%Y-%m-%d") if result.published else "N/A"
            updated = result.updated.strftime("%Y-%m-%d") if result.updated else "N/A"
            pdf_url = result.pdf_url
            entry_id = result.entry_id
            doi = result.doi if result.doi else "N/A"
            journal_ref = result.journal_ref if result.journal_ref else "N/A"
            comment = result.comment if result.comment else "N/A"
            links = "||".join([link.href for link in result.links])

            article_data = "\n".join([
                f"Title: {title}",
                f"Authors: {authors}",
                f"Published: {published}",
                f"Updated: {updated}",
                f"Primary Category: {primary_category}",
                f"All Categories: {categories}",
                f"DOI: {doi}",
                f"Journal Reference: {journal_ref}",
                f"Comment: {comment}",
                f"Entry ID: {entry_id}",
                f"PDF URL: {pdf_url}",
                f"All Links: {links}",
                f"Summary: {summary}",
            ])

            formatted_results.append(article_data)
        return formatted_results

    def search(self, keyword, max_results=10) -> List[str]:
        results = self.arxiv_search(keyword, max_results)
        return self._parse_results(results)
