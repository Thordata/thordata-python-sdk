"""
Social Media Scraper Tools.
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import ToolRequest


class TikTok:
    @dataclass
    class Post(ToolRequest):
        """TikTok Post Information Scraper"""

        SPIDER_ID = "tiktok_posts_by-url"
        SPIDER_NAME = "tiktok.com"
        url: str
        page_turning: int | None = None

    @dataclass
    class Comment(ToolRequest):
        """TikTok Comment Scraper"""

        SPIDER_ID = "tiktok_comment_by-url"
        SPIDER_NAME = "tiktok.com"
        url: str
        page_turning: int | None = None

    @dataclass
    class Profile(ToolRequest):
        """TikTok Profile Information Scraper"""

        SPIDER_ID = "tiktok_profiles_by-url"
        SPIDER_NAME = "tiktok.com"

        url: str  # Profile URL (e.g. https://www.tiktok.com/@user)
        search_url: str | None = None

        country: str | None = None
        page_turning: int | None = None

    @dataclass
    class Shop(ToolRequest):
        """TikTok Shop Information Scraper"""

        SPIDER_ID = "tiktok_shop_by-url"
        SPIDER_NAME = "tiktok.com"
        url: str
        category_url: str | None = None
        keyword: str | None = None
        page_turning: int | None = None


class Facebook:
    @dataclass
    class Posts(ToolRequest):
        """Facebook Posts Scraper"""

        SPIDER_ID = "facebook_post_by-keywords"
        SPIDER_NAME = "facebook.com"
        keyword: str
        recent_posts: bool | None = None
        date: str | None = None  # Year 2025 etc.
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
        profileurl: str | None = None

    @dataclass
    class Post(ToolRequest):
        """Instagram Post Information Scraper"""

        SPIDER_ID = "ins_posts_by-profileurl"
        SPIDER_NAME = "instagram.com"
        profileurl: str
        resultsLimit: int = 10
        start_date: str | None = None
        end_date: str | None = None
        post_type: str | None = None  # Post or Reel

    @dataclass
    class Reel(ToolRequest):
        """Instagram Reel Information Scraper"""

        SPIDER_ID = "ins_reel_by-url"
        SPIDER_NAME = "instagram.com"
        url: str
        num_of_posts: int | None = None

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
        max_number_of_posts: int | None = None
        user_name: str | None = None

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

        start_date: str | None = None
        end_date: str | None = None


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
        job_url: str | None = None
        page_turning: int | None = None
        keyword: str | None = None
        remote: str | None = None  # On_site, Remote, Hybrid


class Reddit:
    @dataclass
    class Posts(ToolRequest):
        """Reddit Post Information Scraper"""

        SPIDER_ID = "reddit_posts_by-url"
        SPIDER_NAME = "reddit.com"
        url: str
        keyword: str | None = None
        subreddit_url: str | None = None
        num_of_posts: int | None = None
        sort_by: str | None = None  # Relevance, Hot, Top, New

    @dataclass
    class Comment(ToolRequest):
        """Reddit Post Comment Scraper"""

        SPIDER_ID = "reddit_comment_by-url"
        SPIDER_NAME = "reddit.com"
        url: str
        days_back: int | None = None
        load_all_replies: bool | None = None
