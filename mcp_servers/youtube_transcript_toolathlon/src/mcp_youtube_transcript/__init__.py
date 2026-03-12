#  __init__.py
#
#  Copyright (c) 2025 Junpei Kawamoto
#
#  This software is released under the MIT License.
#
#  http://opensource.org/licenses/mit-license.php
from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache, partial
from itertools import islice
from typing import Any, AsyncIterator, Tuple
from typing import Final
from urllib.parse import urlparse, parse_qs

import humanize
import requests
from bs4 import BeautifulSoup
from mcp import ServerSession
from mcp.server import FastMCP
from mcp.server.fastmcp import Context
from pydantic import Field, BaseModel, AwareDatetime
from youtube_transcript_api import YouTubeTranscriptApi, FetchedTranscriptSnippet
from youtube_transcript_api.proxies import WebshareProxyConfig, GenericProxyConfig, ProxyConfig
from yt_dlp import YoutubeDL
from yt_dlp.extractor.youtube import YoutubeIE


@dataclass(frozen=True)
class AppContext:
    http_client: requests.Session
    ytt_api: YouTubeTranscriptApi
    dlp: YoutubeDL


@asynccontextmanager
async def _app_lifespan(_server: FastMCP, proxy_config: ProxyConfig | None) -> AsyncIterator[AppContext]:
    # Prepare YoutubeDL params with proxy support
    ytdlp_params: dict[str, Any] = {"quiet": True}
    ytdlp_params.update(_proxy_config_to_ytdlp_params(proxy_config))

    with requests.Session() as http_client, YoutubeDL(params=ytdlp_params, auto_init=False) as dlp:
        ytt_api = YouTubeTranscriptApi(http_client=http_client, proxy_config=proxy_config)
        dlp.add_info_extractor(YoutubeIE())
        yield AppContext(http_client=http_client, ytt_api=ytt_api, dlp=dlp)


class Transcript(BaseModel):
    """Transcript of a YouTube video."""

    title: str = Field(description="Title of the video")
    transcript: str = Field(description="Transcript of the video")
    next_cursor: str | None = Field(description="Cursor to retrieve the next page of the transcript", default=None)


class TranscriptSnippet(BaseModel):
    """Transcript snippet of a YouTube video."""

    text: str = Field(description="Text of the transcript snippet")
    start: float = Field(description="The timestamp at which this transcript snippet appears on screen in seconds.")
    duration: float = Field(description="The duration of how long the snippet in seconds.")

    def __len__(self) -> int:
        return len(self.model_dump_json())

    @classmethod
    def from_fetched_transcript_snippet(
        cls: type[TranscriptSnippet], snippet: FetchedTranscriptSnippet
    ) -> TranscriptSnippet:
        return cls(text=snippet.text, start=snippet.start, duration=snippet.duration)


class TimedTranscript(BaseModel):
    """Transcript of a YouTube video with timestamps."""

    title: str = Field(description="Title of the video")
    snippets: list[TranscriptSnippet] = Field(description="Transcript snippets of the video")
    next_cursor: str | None = Field(description="Cursor to retrieve the next page of the transcript", default=None)


class VideoInfo(BaseModel):
    """Video information."""

    title: str = Field(description="Title of the video")
    description: str = Field(description="Description of the video")
    uploader: str = Field(description="Uploader of the video")
    upload_date: AwareDatetime = Field(description="Upload date of the video")
    duration: str = Field(description="Duration of the video")


def _parse_time_info(date: int, timestamp: int, duration: int) -> Tuple[datetime, str]:
    parsed_date = datetime.strptime(str(date), "%Y%m%d").date()
    parsed_time = datetime.strptime(str(timestamp), "%H%M%S%f").time()
    upload_date = datetime.combine(parsed_date, parsed_time, timezone.utc)
    duration_str = humanize.naturaldelta(timedelta(seconds=duration))
    return upload_date, duration_str


def _proxy_config_to_ytdlp_params(proxy_config: ProxyConfig | None) -> dict[str, str]:
    """
    Convert ProxyConfig to yt-dlp params format.

    Args:
        proxy_config: ProxyConfig object from youtube_transcript_api.proxies

    Returns:
        Dictionary with 'proxy' key if proxy is configured, empty dict otherwise.
    """
    if proxy_config is None:
        return {}

    # Get the requests-format proxy dict (format: {'http': '...', 'https': '...'})
    proxy_dict = proxy_config.to_requests_dict()

    # yt-dlp accepts a single 'proxy' parameter
    # Prefer HTTPS over HTTP since YouTube uses HTTPS
    if "https" in proxy_dict and proxy_dict["https"]:
        return {"proxy": proxy_dict["https"]}
    elif "http" in proxy_dict and proxy_dict["http"]:
        return {"proxy": proxy_dict["http"]}

    return {}


def _parse_video_id(url: str) -> str:
    parsed_url = urlparse(url)
    if parsed_url.hostname == "youtu.be":
        return parsed_url.path.lstrip("/")
    else:
        q = parse_qs(parsed_url.query).get("v")
        if q is None:
            raise ValueError(f"couldn't find a video ID from the provided URL: {url}.")
        return q[0]


@lru_cache
def _get_transcript_snippets(ctx: AppContext, video_id: str, lang: str) -> Tuple[str, list[FetchedTranscriptSnippet]]:
    if lang == "en":
        languages = ["en"]
    else:
        languages = [lang, "en"]

    page = ctx.http_client.get(
        f"https://www.youtube.com/watch?v={video_id}", headers={"Accept-Language": ",".join(languages)}
    )
    page.raise_for_status()
    soup = BeautifulSoup(page.text, "html.parser")
    title = soup.title.string if soup.title and soup.title.string else "Transcript"

    transcripts = ctx.ytt_api.fetch(video_id, languages=languages)
    return title, transcripts.snippets


@lru_cache
def _get_video_info(ctx: AppContext, video_url: str) -> VideoInfo:
    res = ctx.dlp.extract_info(video_url, download=False)
    upload_date, duration = _parse_time_info(res["upload_date"], res["timestamp"], res["duration"])
    return VideoInfo(
        title=res["title"],
        description=res["description"],
        uploader=res["uploader"],
        upload_date=upload_date,
        duration=duration,
    )


def server(
    response_limit: int | None = None,
    webshare_proxy_username: str | None = None,
    webshare_proxy_password: str | None = None,
    http_proxy: str | None = None,
    https_proxy: str | None = None,
) -> FastMCP:
    """Initializes the MCP server."""

    proxy_config: ProxyConfig | None = None
    if webshare_proxy_username and webshare_proxy_password:
        proxy_config = WebshareProxyConfig(webshare_proxy_username, webshare_proxy_password)
    elif http_proxy or https_proxy:
        proxy_config = GenericProxyConfig(http_proxy, https_proxy)

    mcp = FastMCP("Youtube Transcript", lifespan=partial(_app_lifespan, proxy_config=proxy_config))

    @mcp.tool()
    async def get_transcript(
        ctx: Context[ServerSession, AppContext],
        url: str = Field(description="The URL of the YouTube video"),
        lang: str = Field(description="The preferred language for the transcript", default="en"),
        next_cursor: str | None = Field(description="Cursor to retrieve the next page of the transcript", default=None),
    ) -> Transcript:
        """Retrieves the transcript of a YouTube video."""

        title, snippets = _get_transcript_snippets(ctx.request_context.lifespan_context, _parse_video_id(url), lang)
        transcripts = (item.text for item in snippets)

        if response_limit is None or response_limit <= 0:
            return Transcript(title=title, transcript="\n".join(transcripts))

        res = ""
        cursor = None
        for i, line in islice(enumerate(transcripts), int(next_cursor or 0), None):
            if len(res) + len(line) + 1 > response_limit:
                cursor = str(i)
                break
            res += f"{line}\n"

        return Transcript(title=title, transcript=res[:-1], next_cursor=cursor)

    @mcp.tool()
    async def get_timed_transcript(
        ctx: Context[ServerSession, AppContext],
        url: str = Field(description="The URL of the YouTube video"),
        lang: str = Field(description="The preferred language for the transcript", default="en"),
        next_cursor: str | None = Field(description="Cursor to retrieve the next page of the transcript", default=None),
    ) -> TimedTranscript:
        """Retrieves the transcript of a YouTube video with timestamps."""

        title, snippets = _get_transcript_snippets(ctx.request_context.lifespan_context, _parse_video_id(url), lang)

        if response_limit is None or response_limit <= 0:
            return TimedTranscript(
                title=title, snippets=[TranscriptSnippet.from_fetched_transcript_snippet(s) for s in snippets]
            )

        res = []
        size = len(title) + 1
        cursor = None
        for i, s in islice(enumerate(snippets), int(next_cursor or 0), None):
            snippet = TranscriptSnippet.from_fetched_transcript_snippet(s)
            if size + len(snippet) + 1 > response_limit:
                cursor = str(i)
                break
            res.append(snippet)

        return TimedTranscript(title=title, snippets=res, next_cursor=cursor)

    @mcp.tool()
    def get_video_info(
        ctx: Context[ServerSession, AppContext],
        url: str = Field(description="The URL of the YouTube video"),
    ) -> VideoInfo:
        """Retrieves the video information."""
        return _get_video_info(ctx.request_context.lifespan_context, url)

    return mcp


__all__: Final = ["server", "Transcript", "TimedTranscript", "TranscriptSnippet", "VideoInfo"]
