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
        """YouTube Profile Scraper by Keyword. Uses video_builder."""

        SPIDER_ID = "youtube_profiles_by-keyword"
        SPIDER_NAME = "youtube.com"

        keyword: str
        page_turning: int = 1
        common_settings: CommonSettings = field(default_factory=CommonSettings)

    @dataclass
    class ProfileByUrl(VideoToolRequest):
        """YouTube Profile Scraper by URL. Uses video_builder."""

        SPIDER_ID = "youtube_profiles_by-url"
        SPIDER_NAME = "youtube.com"

        url: str  # Channel URL
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
    class VideoInfo(VideoToolRequest):
        """YouTube Video Basic Information Scraper. Uses video_builder."""

        SPIDER_ID = "youtube_product_by-id"
        SPIDER_NAME = "youtube.com"

        video_id: str
        common_settings: CommonSettings = field(default_factory=CommonSettings)

    @dataclass
    class VideoPostByUrl(ToolRequest):
        """YouTube Video Post Scraper by URL. Uses standard builder."""

        SPIDER_ID = "youtube_video-post_by-url"
        SPIDER_NAME = "youtube.com"

        url: str  # Channel Video URL
        order_by: str | None = None
        start_index: str | None = None
        num_of_posts: str | None = None

    @dataclass
    class VideoPostBySearchFilters(ToolRequest):
        """YouTube Video Post Scraper by Search Filters. Uses standard builder."""

        SPIDER_ID = "youtube_video-post_by-search-filters"
        SPIDER_NAME = "youtube.com"

        keyword_search: str
        features: str | None = None
        type: str | None = None  # Videos
        duration: str | None = None
        upload_date: str | None = None
        num_of_posts: str | None = None

    @dataclass
    class VideoPostByHashtag(ToolRequest):
        """YouTube Video Post Scraper by Hashtag. Uses standard builder."""

        SPIDER_ID = "youtube_video-post_by-hashtag"
        SPIDER_NAME = "youtube.com"

        hashtag: str
        num_of_posts: str | None = None

    @dataclass
    class VideoPostByPodcastUrl(ToolRequest):
        """YouTube Video Post Scraper by Podcast URL. Uses standard builder."""

        SPIDER_ID = "youtube_video-post_by-podcast-url"
        SPIDER_NAME = "youtube.com"

        url: str  # Playlist URL
        num_of_posts: str | None = None

    @dataclass
    class VideoPostByKeyword(ToolRequest):
        """YouTube Video Post Scraper by Keyword. Uses standard builder."""

        SPIDER_ID = "youtube_video-post_by-keyword"
        SPIDER_NAME = "youtube.com"

        keyword: str
        num_of_posts: str | None = None

    @dataclass
    class VideoPostByExplore(ToolRequest):
        """YouTube Video Post Scraper by Explore URL. Uses standard builder."""

        SPIDER_ID = "youtube_video-post_by-explore"
        SPIDER_NAME = "youtube.com"

        url: str
        all_tabs: str | None = None
