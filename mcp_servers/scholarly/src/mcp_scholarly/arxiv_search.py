import arxiv
from typing import List

client = arxiv.Client()


class ArxivSearch:
    def __init__(self):
        self.client = arxiv.Client()

    def arxiv_search(self, keyword, max_results=10):
        search = arxiv.Search(query=keyword, max_results=max_results, sort_by=arxiv.SortCriterion.SubmittedDate)
        results = self.client.results(search)
        all_results = list(results)
        return all_results

    @staticmethod
    def _parse_results(results):
        formatted_results = []

        for result in results:
            title = result.title
            summary = result.summary
            links = "||".join([link.href for link in result.links])
            pdf_url = result.pdf_url

            article_data = "\n".join([
                f"Title: {title}",
                f"Summary: {summary}",
                f"Links: {links}",
                f"PDF URL: {pdf_url}",
            ])

            formatted_results.append(article_data)
        return formatted_results

    def search(self, keyword, max_results=10) -> List[str]:
        results = self.arxiv_search(keyword, max_results)
        return self._parse_results(results)
