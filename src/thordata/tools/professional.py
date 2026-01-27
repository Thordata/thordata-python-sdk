"""
Professional Platform Scraper Tools (Indeed, Glassdoor, Crunchbase, etc.)
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import ToolRequest


class Indeed:
    """Namespace for Indeed tools."""

    @dataclass
    class JobByUrl(ToolRequest):
        """Indeed Job Listings Scraper by Job URL"""

        SPIDER_ID = "indeed_job-listings_by-job-url"
        SPIDER_NAME = "indeed.com"
        job_url: str

    @dataclass
    class JobByKeyword(ToolRequest):
        """Indeed Job Listings Scraper by Keyword"""

        SPIDER_ID = "indeed_job-listings_by-keyword"
        SPIDER_NAME = "indeed.com"
        keyword: str
        location: str
        country: str | None = None
        domain: str | None = None
        date_posted: str | None = None
        posted_by: str | None = None
        pay: str | None = None
        location_radius: str | None = None

    @dataclass
    class CompanyByListUrl(ToolRequest):
        """Indeed Companies Info Scraper by Company List URL"""

        SPIDER_ID = "indeed_companies-info_by-company-list-url"
        SPIDER_NAME = "indeed.com"
        company_list_url: str

    @dataclass
    class CompanyByKeyword(ToolRequest):
        """Indeed Companies Info Scraper by Keyword"""

        SPIDER_ID = "indeed_companies-info_by-keyword"
        SPIDER_NAME = "indeed.com"
        keyword: str

    @dataclass
    class CompanyByIndustryAndState(ToolRequest):
        """Indeed Companies Info Scraper by Industry and State"""

        SPIDER_ID = "indeed_companies-info_by-industry-and-state"
        SPIDER_NAME = "indeed.com"
        industry: str
        state: str | None = None

    @dataclass
    class CompanyByUrl(ToolRequest):
        """Indeed Companies Info Scraper by Company URL"""

        SPIDER_ID = "indeed_companies-info_by-company-url"
        SPIDER_NAME = "indeed.com"
        company_url: str


class Glassdoor:
    """Namespace for Glassdoor tools."""

    @dataclass
    class CompanyByUrl(ToolRequest):
        """Glassdoor Company Overview Information Scraper by URL"""

        SPIDER_ID = "glassdoor_company_by-url"
        SPIDER_NAME = "glassdoor.com"
        url: str

    @dataclass
    class CompanyByInputFilter(ToolRequest):
        """Glassdoor Company Overview Information Scraper by Input Filter"""

        SPIDER_ID = "glassdoor_company_by-inputfilter"
        SPIDER_NAME = "glassdoor.com"
        company_name: str
        location: str | None = None
        industries: str | None = None
        Job_title: str | None = None  # Note: capital J in API

    @dataclass
    class CompanyByKeywords(ToolRequest):
        """Glassdoor Company Overview Information Scraper by Keywords"""

        SPIDER_ID = "glassdoor_company_by-keywords"
        SPIDER_NAME = "glassdoor.com"
        search_url: str
        max_search_results: int | None = None

    @dataclass
    class CompanyByListUrl(ToolRequest):
        """Glassdoor Company Overview Information Scraper by List URL"""

        SPIDER_ID = "glassdoor_company_by-listurl"
        SPIDER_NAME = "glassdoor.com"
        url: str

    @dataclass
    class JobByUrl(ToolRequest):
        """Glassdoor Job Information Scraper by URL"""

        SPIDER_ID = "glassdoor_joblistings_by-url"
        SPIDER_NAME = "glassdoor.com"
        url: str

    @dataclass
    class JobByKeywords(ToolRequest):
        """Glassdoor Job Information Scraper by Keywords"""

        SPIDER_ID = "glassdoor_joblistings_by-keywords"
        SPIDER_NAME = "glassdoor.com"
        keyword: str
        location: str
        country: str | None = None

    @dataclass
    class JobByListUrl(ToolRequest):
        """Glassdoor Job Information Scraper by List URL"""

        SPIDER_ID = "glassdoor_joblistings_by-listurl"
        SPIDER_NAME = "glassdoor.com"
        url: str


class Crunchbase:
    """Namespace for Crunchbase tools."""

    @dataclass
    class CompanyByUrl(ToolRequest):
        """Crunchbase Company Information Scraper by URL"""

        SPIDER_ID = "crunchbase_company_by-url"
        SPIDER_NAME = "crunchbase.com"
        url: str

    @dataclass
    class CompanyByKeywords(ToolRequest):
        """Crunchbase Company Information Scraper by Keywords"""

        SPIDER_ID = "crunchbase_company_by-keywords"
        SPIDER_NAME = "crunchbase.com"
        keyword: str
