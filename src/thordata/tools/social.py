"""
Social Media Scraper Tools.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .base import ToolRequest


class TikTok:
    @dataclass
    class Post(ToolRequest):
        """TikTok Post Information Scraper"""

        SPIDER_ID = "tiktok_posts_by-url"
        SPIDER_NAME = "tiktok.com"
        url: str
        page_turning: Optional[int] = None

    @dataclass
    class Comment(ToolRequest):
        """TikTok Comment Scraper"""

        SPIDER_ID = "tiktok_comment_by-url"
        SPIDER_NAME = "tiktok.com"
        url: str
        page_turning: Optional[int] = None

    @dataclass
    class Profile(ToolRequest):
        """TikTok Profile Information Scraper"""

        SPIDER_ID = "tiktok_profiles_by-url"
        SPIDER_NAME = "tiktok.com"

        url: str  # Profile URL (e.g. https://www.tiktok.com/@user)
        search_url: Optional[str] = None

        country: Optional[str] = None
        page_turning: Optional[int] = None

    @dataclass
    class Shop(ToolRequest):
        """TikTok Shop Information Scraper"""

        SPIDER_ID = "tiktok_shop_by-url"
        SPIDER_NAME = "tiktok.com"
        url: str
        category_url: Optional[str] = None
        keyword: Optional[str] = None
        page_turning: Optional[int] = None


class Facebook:
    @dataclass
    class Posts(ToolRequest):
        """Facebook Posts Scraper"""

        SPIDER_ID = "facebook_post_by-keywords"
        SPIDER_NAME = "facebook.com"
        keyword: str
        recent_posts: Optional[bool] = None
        date: Optional[str] = None  # Year 2025 etc.
        number: int = 10

    @dataclass
    class PostDetails(ToolRequest):
        """Facebook Post Details Scraper"""

        SPIDER_ID = "facebook_post_by-posts-url"
        SPIDER_NAME = "facebook.com"
        url: str


class Instagram:
    @dataclass
    class Profile(ToolRequest):
        """Instagram Profile Scraper"""

        SPIDER_ID = "ins_profiles_by-username"
        SPIDER_NAME = "instagram.com"
        username: str
        profileurl: Optional[str] = None

    @dataclass
    class Post(ToolRequest):
        """Instagram Post Information Scraper"""

        SPIDER_ID = "ins_posts_by-profileurl"
        SPIDER_NAME = "instagram.com"
        profileurl: str
        resultsLimit: int = 10
        start_date: Optional[str] = None
        end_date: Optional[str] = None
        post_type: Optional[str] = None  # Post or Reel

    @dataclass
    class Reel(ToolRequest):
        """Instagram Reel Information Scraper"""

        SPIDER_ID = "ins_reel_by-url"
        SPIDER_NAME = "instagram.com"
        url: str
        num_of_posts: Optional[int] = None

    @dataclass
    class Comment(ToolRequest):
        """Instagram Post Comment Scraper"""

        SPIDER_ID = "ins_comment_by-posturl"
        SPIDER_NAME = "instagram.com"
        posturl: str


class Twitter:
    @dataclass
    class Profile(ToolRequest):
        """Twitter(X) Profile Scraper"""

        SPIDER_ID = "twitter_profiles_by-url"
        SPIDER_NAME = "twitter.com"
        url: str
        max_number_of_posts: Optional[int] = None
        user_name: Optional[str] = None

    @dataclass
    class Post(ToolRequest):
        """
        Twitter(X) Post Information Scraper
        Updates based on integration snippet:
        - SPIDER_NAME is 'x.com'
        - Only 'url' is required.
        """

        SPIDER_ID = "twitter_by-posturl_by-url"
        SPIDER_NAME = "x.com"  # Updated from snippet

        url: str  # Post URL (e.g. https://x.com/user/status/123)

        start_date: Optional[str] = None
        end_date: Optional[str] = None


class LinkedIn:
    @dataclass
    class Company(ToolRequest):
        """LinkedIn Company Information Scraper"""

        SPIDER_ID = "linkedin_company_information_by-url"
        SPIDER_NAME = "linkedin.com"
        url: str

    @dataclass
    class Jobs(ToolRequest):
        """LinkedIn Job Listing Scraper"""

        SPIDER_ID = "linkedin_job_listings_information_by-job-listing-url"
        SPIDER_NAME = "linkedin.com"
        job_listing_url: str
        location: str
        job_url: Optional[str] = None
        page_turning: Optional[int] = None
        keyword: Optional[str] = None
        remote: Optional[str] = None  # On_site, Remote, Hybrid


class Reddit:
    @dataclass
    class Posts(ToolRequest):
        """Reddit Post Information Scraper"""

        SPIDER_ID = "reddit_posts_by-url"
        SPIDER_NAME = "reddit.com"
        url: str
        keyword: Optional[str] = None
        subreddit_url: Optional[str] = None
        num_of_posts: Optional[int] = None
        sort_by: Optional[str] = None  # Relevance, Hot, Top, New

    @dataclass
    class Comment(ToolRequest):
        """Reddit Post Comment Scraper"""

        SPIDER_ID = "reddit_comment_by-url"
        SPIDER_NAME = "reddit.com"
        url: str
        days_back: Optional[int] = None
        load_all_replies: Optional[bool] = None
