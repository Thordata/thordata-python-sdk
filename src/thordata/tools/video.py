"""
Video & Audio Scraper Tools (YouTube, etc.)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..types.common import CommonSettings
from .base import ToolRequest, VideoToolRequest


class YouTube:
    """Namespace for YouTube tools."""

    @dataclass
    class VideoDownload(VideoToolRequest):
        """YouTube Video File Scraper (Download). Uses video_builder."""

        SPIDER_ID = "youtube_video_by-url"
        SPIDER_NAME = "youtube.com"

        url: str  # Video URL
        common_settings: CommonSettings = field(default_factory=CommonSettings)

    @dataclass
    class AudioDownload(VideoToolRequest):
        """YouTube Audio File Scraper (Download). Uses video_builder."""

        SPIDER_ID = "youtube_audio_by-url"
        SPIDER_NAME = "youtube.com"

        url: str
        common_settings: CommonSettings = field(default_factory=CommonSettings)

    @dataclass
    class SubtitleDownload(VideoToolRequest):
        """YouTube Subtitle File Scraper. Uses video_builder."""

        SPIDER_ID = "youtube_transcript_by-id"
        SPIDER_NAME = "youtube.com"

        video_id: str
        subtitles_type: str | None = None  # Auto generated / user uploaded
        common_settings: CommonSettings = field(default_factory=CommonSettings)

    @dataclass
    class Profile(VideoToolRequest):
        """YouTube Profile Scraper. Uses video_builder."""

        SPIDER_ID = "youtube_profiles_by-keyword"
        SPIDER_NAME = "youtube.com"

        url: str  # Channel URL
        page_turning: int = 1
        keyword: str | None = None
        common_settings: CommonSettings = field(default_factory=CommonSettings)

    @dataclass
    class Comments(VideoToolRequest):
        """YouTube Comment Information Scraper. Uses video_builder."""

        SPIDER_ID = "youtube_comment_by-id"
        SPIDER_NAME = "youtube.com"

        video_id: str
        num_of_comments: int | None = None
        sort_by: str | None = None  # Top comments / Newest first
        common_settings: CommonSettings = field(default_factory=CommonSettings)

    @dataclass
    class VideoInfo(ToolRequest):
        """YouTube Video Post Scraper (Metadata only). Standard builder."""

        # Note: This one does NOT inherit from VideoToolRequest because it uses the standard builder
        # and doesn't support common_settings in the same way.
        SPIDER_ID = "youtube_video-post_by-url"
        SPIDER_NAME = "youtube.com"

        url: str  # Channel Video URL
        num_of_posts: str | None = None
