# klavis_google_news/tools/search_news.py
from typing import List
from mcp import Tool
from dateutil import parser as date_parser
from google_news.tools.base import SerpApiClient
from google_news.tools.articles import (
    Article,
    ArticleSearchIn,
    ArticleSearchOut,
    ArticleCluster,
)
from google_news.tools.utils import remove_none_values, iso8601, schema_from_model

spec = Tool(
    name="search_news",
    description="Keyword search across Google News via SerpAPI. Use coherent filters and queries into making the websearch.",
    inputSchema=schema_from_model(ArticleSearchIn),
    outputSchema=schema_from_model(ArticleSearchOut),
)


async def run(args: ArticleSearchIn) -> ArticleSearchOut:
    cli = SerpApiClient()
    params = remove_none_values(
        {
            "engine": "google_news",
            "q": args.query,
            "hl": args.language,
            "gl": args.country,
            "after": iso8601(args.from_date),
            "before": iso8601(args.to_date),
            "sort_by": args.sort_by,
            "page": args.page,
            "num": 10,
        }
    )
    raw = await cli.get("search.json", params=params)

    articles: List[Article] = []
    clusters: List[ArticleCluster] = []

    for item in raw.get("news_results", []):
        if "stories" in item:
            # build a cluster
            group = []
            for story in item["stories"]:
                # parse date safely
                try:
                    dt = date_parser.parse(story.get("date", ""))
                    iso = dt.isoformat() + "Z"
                except Exception:
                    iso = None
                group.append(
                    Article(
                        title=story.get("title", ""),
                        link=story.get("link", ""),
                        source=story.get("source"),
                        published_at=iso,
                        thumbnail_url=story.get("thumbnail"),
                    )
                )
            clusters.append(
                ArticleCluster(
                    serpapi_link=item.get("serpapi_link"),
                    stories=group,
                )
            )
        else:
            # single article
            try:
                dt = date_parser.parse(item.get("date", ""))
                iso = dt.isoformat() + "Z"
            except Exception:
                iso = None

            articles.append(
                Article(
                    title=item.get("title", ""),
                    link=item.get("link", ""),
                    source=item.get("source"),
                    published_at=iso,
                    thumbnail_url=item.get("thumbnail"),
                )
            )

    return ArticleSearchOut(
        articles=articles,
        clusters=clusters,
        next_page=raw.get("serpapi_pagination", {}).get("next"),
    )
