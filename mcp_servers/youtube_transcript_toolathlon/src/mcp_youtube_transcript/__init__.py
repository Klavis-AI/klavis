#  __init__.py
#
#  Copyright (c) 2025 Junpei Kawamoto
#
#  This software is released under the MIT License.
#
#  http://opensource.org/licenses/mit-license.php
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from itertools import islice
from typing import Any, Tuple
from typing import Final
from urllib.parse import urlparse, parse_qs

import humanize
import requests
from bs4 import BeautifulSoup
from mcp.server import FastMCP
from pydantic import Field, BaseModel, AwareDatetime
from youtube_transcript_api import YouTubeTranscriptApi, FetchedTranscriptSnippet
from youtube_transcript_api.proxies import WebshareProxyConfig, GenericProxyConfig, ProxyConfig
from yt_dlp import YoutubeDL
from yt_dlp.extractor.youtube import YoutubeIE


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


def _get_transcript_snippets(
    proxy_config: ProxyConfig | None, video_id: str, lang: str
) -> Tuple[str, list[FetchedTranscriptSnippet]]:
    languages = ["en"] if lang == "en" else [lang, "en"]
    with requests.Session() as http_client:
        page = http_client.get(
            f"https://www.youtube.com/watch?v={video_id}",
            headers={"Accept-Language": ",".join(languages)},
        )
        page.raise_for_status()
        soup = BeautifulSoup(page.text, "html.parser")
        title = soup.title.string if soup.title and soup.title.string else "Transcript"
        ytt_api = YouTubeTranscriptApi(http_client=http_client, proxy_config=proxy_config)
        transcripts = ytt_api.fetch(video_id, languages=languages)
    return title, transcripts.snippets


def _get_video_info(proxy_config: ProxyConfig | None, video_url: str) -> VideoInfo:
    ytdlp_params: dict[str, Any] = {"quiet": True}
    ytdlp_params.update(_proxy_config_to_ytdlp_params(proxy_config))
    with YoutubeDL(params=ytdlp_params, auto_init=False) as dlp:
        dlp.add_info_extractor(YoutubeIE())
        res = dlp.extract_info(video_url, download=False)
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

    mcp = FastMCP("Youtube Transcript")

    @mcp.tool()
    async def get_transcript(
        url: str = Field(description="The URL of the YouTube video"),
        lang: str = Field(description="The preferred language for the transcript", default="en"),
        next_cursor: str | None = Field(description="Cursor to retrieve the next page of the transcript", default=None),
    ) -> Transcript:
        """Retrieves the transcript of a YouTube video."""

        title, snippets = await asyncio.to_thread(
            _get_transcript_snippets, proxy_config, _parse_video_id(url), lang
        )
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
        url: str = Field(description="The URL of the YouTube video"),
        lang: str = Field(description="The preferred language for the transcript", default="en"),
        next_cursor: str | None = Field(description="Cursor to retrieve the next page of the transcript", default=None),
    ) -> TimedTranscript:
        """Retrieves the transcript of a YouTube video with timestamps."""

        title, snippets = await asyncio.to_thread(
            _get_transcript_snippets, proxy_config, _parse_video_id(url), lang
        )

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
    async def get_video_info(
        url: str = Field(description="The URL of the YouTube video"),
    ) -> VideoInfo:
        """Retrieves the video information."""
        return await asyncio.to_thread(_get_video_info, proxy_config, url)

    return mcp


__all__: Final = ["server", "Transcript", "TimedTranscript", "TranscriptSnippet", "VideoInfo"]
