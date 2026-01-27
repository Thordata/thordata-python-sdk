"""
Social Media Scraper Tools.
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import ToolRequest


class TikTok:
    @dataclass
    class Post(ToolRequest):
        """TikTok Post Information Scraper by URL"""

        SPIDER_ID = "tiktok_posts_by-url"
        SPIDER_NAME = "tiktok.com"
        url: str
        country: str | None = None

    @dataclass
    class PostsByKeywords(ToolRequest):
        """TikTok Post Information Scraper by Keywords"""

        SPIDER_ID = "tiktok_posts_by-keywords"
        SPIDER_NAME = "tiktok.com"
        search_keyword: str
        num_of_posts: int | None = None
        posts_to_not_include: str | None = None
        country: str | None = None

    @dataclass
    class PostsByProfileUrl(ToolRequest):
        """TikTok Post Information Scraper by Profile URL"""

        SPIDER_ID = "tiktok_posts_by-profileurl"
        SPIDER_NAME = "tiktok.com"
        url: str
        start_date: str | None = None
        end_date: str | None = None
        num_of_posts: int | None = None
        what_to_collect: str | None = None
        post_type: str | None = None
        posts_to_not_include: str | None = None
        country: str | None = None

    @dataclass
    class PostsByListUrl(ToolRequest):
        """TikTok Post Information Scraper by List URL"""

        SPIDER_ID = "tiktok_posts_by-listurl"
        SPIDER_NAME = "tiktok.com"
        url: str
        num_of_posts: int | None = None

    @dataclass
    class Comment(ToolRequest):
        """TikTok Comment Scraper"""

        SPIDER_ID = "tiktok_comment_by-url"
        SPIDER_NAME = "tiktok.com"
        url: str
        page_turning: int | None = None

    @dataclass
    class Profile(ToolRequest):
        """TikTok Profile Information Scraper by URL"""

        SPIDER_ID = "tiktok_profiles_by-url"
        SPIDER_NAME = "tiktok.com"
        url: str  # Profile URL (e.g. https://www.tiktok.com/@user)
        country: str | None = None

    @dataclass
    class ProfilesByListUrl(ToolRequest):
        """TikTok Profile Information Scraper by List URL"""

        SPIDER_ID = "tiktok_profiles_by-listurl"
        SPIDER_NAME = "tiktok.com"
        search_url: str
        country: str | None = None
        page_turning: int | None = None

    @dataclass
    class Shop(ToolRequest):
        """TikTok Shop Information Scraper by URL"""

        SPIDER_ID = "tiktok_shop_by-url"
        SPIDER_NAME = "tiktok.com"
        url: str

    @dataclass
    class ShopByCategoryUrl(ToolRequest):
        """TikTok Shop Information Scraper by Category URL"""

        SPIDER_ID = "tiktok_shop_by-category-url"
        SPIDER_NAME = "tiktok.com"
        category_url: str

    @dataclass
    class ShopByKeywords(ToolRequest):
        """TikTok Shop Information Scraper by Keywords"""

        SPIDER_ID = "tiktok_shop_by-keywords"
        SPIDER_NAME = "tiktok.com"
        keyword: str
        domain: str = "https://www.tiktok.com/shop"
        page_turning: int | None = None


class Facebook:
    @dataclass
    class PostDetails(ToolRequest):
        """Facebook Post Details Scraper"""

        SPIDER_ID = "facebook_post_by-posts-url"
        SPIDER_NAME = "facebook.com"
        url: str

    @dataclass
    class Posts(ToolRequest):
        """Facebook Posts Scraper by Keywords"""

        SPIDER_ID = "facebook_post_by-keywords"
        SPIDER_NAME = "facebook.com"
        keyword: str
        recent_posts: bool | None = None
        date: str | None = None  # Year 2025 etc.
        number: int = 10

    @dataclass
    class EventByEventListUrl(ToolRequest):
        """Facebook Events Scraper by Event List URL"""

        SPIDER_ID = "facebook_event_by-eventlist-url"
        SPIDER_NAME = "facebook.com"
        url: str
        upcoming_events_only: str | None = None

    @dataclass
    class EventBySearchUrl(ToolRequest):
        """Facebook Events Scraper by Search URL"""

        SPIDER_ID = "facebook_event_by-search-url"
        SPIDER_NAME = "facebook.com"
        url: str

    @dataclass
    class EventByEventsUrl(ToolRequest):
        """Facebook Events Scraper by Events URL"""

        SPIDER_ID = "facebook_event_by-events-url"
        SPIDER_NAME = "facebook.com"
        url: str

    @dataclass
    class Profile(ToolRequest):
        """Facebook Profile Scraper"""

        SPIDER_ID = "facebook_profile_by-profiles-url"
        SPIDER_NAME = "facebook.com"
        url: str

    @dataclass
    class Comment(ToolRequest):
        """Facebook Post Comments Scraper"""

        SPIDER_ID = "facebook_comment_by-comments-url"
        SPIDER_NAME = "facebook.com"
        url: str
        get_all_replies: str | None = None
        limit_records: str | None = None
        comments_sort: str | None = None  # All comments


class Instagram:
    @dataclass
    class Profile(ToolRequest):
        """Instagram Profile Scraper by Username"""

        SPIDER_ID = "ins_profiles_by-username"
        SPIDER_NAME = "instagram.com"
        username: str

    @dataclass
    class ProfileByUrl(ToolRequest):
        """Instagram Profile Scraper by Profile URL"""

        SPIDER_ID = "ins_profiles_by-profileurl"
        SPIDER_NAME = "instagram.com"
        profileurl: str

    @dataclass
    class Post(ToolRequest):
        """Instagram Post Information Scraper by Profile URL"""

        SPIDER_ID = "ins_posts_by-profileurl"
        SPIDER_NAME = "instagram.com"
        profileurl: str
        resultsLimit: int = 10
        start_date: str | None = None
        end_date: str | None = None
        post_type: str | None = None  # Post or Reel

    @dataclass
    class PostByUrl(ToolRequest):
        """Instagram Post Information Scraper by Post URL"""

        SPIDER_ID = "ins_posts_by-posturl"
        SPIDER_NAME = "instagram.com"
        posturl: str

    @dataclass
    class Reel(ToolRequest):
        """Instagram Reel Information Scraper by URL"""

        SPIDER_ID = "ins_reel_by-url"
        SPIDER_NAME = "instagram.com"
        url: str

    @dataclass
    class AllReel(ToolRequest):
        """Instagram All Reel Information Scraper by URL"""

        SPIDER_ID = "ins_allreel_by-url"
        SPIDER_NAME = "instagram.com"
        url: str
        num_of_posts: int | None = None
        posts_to_not_include: str | None = None
        start_date: str | None = None
        end_date: str | None = None

    @dataclass
    class ReelByListUrl(ToolRequest):
        """Instagram Reel Information Scraper by List URL"""

        SPIDER_ID = "ins_reel_by-listurl"
        SPIDER_NAME = "instagram.com"
        url: str
        num_of_posts: int | None = None
        posts_to_not_include: str | None = None
        start_date: str | None = None
        end_date: str | None = None

    @dataclass
    class Comment(ToolRequest):
        """Instagram Post Comment Scraper"""

        SPIDER_ID = "ins_comment_by-posturl"
        SPIDER_NAME = "instagram.com"
        posturl: str


class Twitter:
    @dataclass
    class Profile(ToolRequest):
        """Twitter(X) Profile Scraper by Profile URL"""

        SPIDER_ID = "twitter_profile_by-profileurl"
        SPIDER_NAME = "x.com"
        url: str

    @dataclass
    class ProfileByUsername(ToolRequest):
        """Twitter(X) Profile Scraper by Username"""

        SPIDER_ID = "twitter_profile_by-username"
        SPIDER_NAME = "x.com"
        user_name: str

    @dataclass
    class Post(ToolRequest):
        """Twitter(X) Post Information Scraper by Post URL"""

        SPIDER_ID = "twitter_post_by-posturl"
        SPIDER_NAME = "x.com"
        url: str  # Post URL (e.g. https://x.com/user/status/123)

    @dataclass
    class PostByProfileUrl(ToolRequest):
        """Twitter(X) Post Information Scraper by Profile URL"""

        SPIDER_ID = "twitter_post_by-profileurl"
        SPIDER_NAME = "x.com"
        url: str  # Profile URL


class LinkedIn:
    @dataclass
    class Company(ToolRequest):
        """LinkedIn Company Information Scraper"""

        SPIDER_ID = "linkedin_company_information_by-url"
        SPIDER_NAME = "linkedin.com"
        url: str

    @dataclass
    class Jobs(ToolRequest):
        """LinkedIn Job Listing Scraper by Job Listing URL"""

        SPIDER_ID = "linkedin_job_listings_information_by-job-listing-url"
        SPIDER_NAME = "linkedin.com"
        job_listing_url: str
        page_turning: int | None = None

    @dataclass
    class JobByUrl(ToolRequest):
        """LinkedIn Job Listing Scraper by Job URL"""

        SPIDER_ID = "linkedin_job_listings_information_by-job-url"
        SPIDER_NAME = "linkedin.com"
        job_url: str

    @dataclass
    class JobByKeyword(ToolRequest):
        """LinkedIn Job Listing Scraper by Keyword"""

        SPIDER_ID = "linkedin_job_listings_information_by-keyword"
        SPIDER_NAME = "linkedin.com"
        location: str
        keyword: str
        time_range: str | None = None
        experience_level: str | None = None
        job_type: str | None = None
        remote: str | None = None
        company: str | None = None
        selective_search: str | None = None
        jobs_to_not_include: str | None = None
        location_radius: str | None = None
        page_turning: int | None = None


class Reddit:
    @dataclass
    class Posts(ToolRequest):
        """Reddit Post Information Scraper by URL"""

        SPIDER_ID = "reddit_posts_by-url"
        SPIDER_NAME = "reddit.com"
        url: str

    @dataclass
    class PostsByKeywords(ToolRequest):
        """Reddit Post Information Scraper by Keywords"""

        SPIDER_ID = "reddit_posts_by-keywords"
        SPIDER_NAME = "reddit.com"
        keyword: str
        date: str | None = None  # All time
        num_of_posts: int | None = None
        sort_by: str | None = None

    @dataclass
    class PostsBySubredditUrl(ToolRequest):
        """Reddit Post Information Scraper by Subreddit URL"""

        SPIDER_ID = "reddit_posts_by-subredditurl"
        SPIDER_NAME = "reddit.com"
        url: str
        sort_by: str | None = None
        num_of_posts: int | None = None
        sort_by_time: str | None = None  # All Time

    @dataclass
    class Comment(ToolRequest):
        """Reddit Post Comment Scraper"""

        SPIDER_ID = "reddit_comment_by-url"
        SPIDER_NAME = "reddit.com"
        url: str
        days_back: int | None = None
        load_all_replies: str | None = None
        comment_limit: int | None = None
