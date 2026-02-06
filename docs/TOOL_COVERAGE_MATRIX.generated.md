# Thordata Web Scraper Tool Coverage (Generated)

> This file is generated from the live Python SDK registry.

> Do not edit manually. Re-generate via `python -m scripts.generate_tool_coverage_matrix`.


## Summary

- Total tools: **110**
- **code**: 3
- **ecommerce**: 24
- **professional**: 15
- **search**: 10
- **social**: 37
- **travel**: 8
- **video**: 13


## Group: `code`

| spider_id | spider_name | key | class | module | params | type |
|-----------|------------|-----|-------|--------|--------|------|
| `github_repository_by-repo-url` | `github.com` | `code.github_repository_by-repo-url` | `Repository` | `thordata.tools.code` | repo_url |  |
| `github_repository_by-search-url` | `github.com` | `code.github_repository_by-search-url` | `RepositoryBySearchUrl` | `thordata.tools.code` | search_url, page_turning, max_num |  |
| `github_repository_by-url` | `github.com` | `code.github_repository_by-url` | `RepositoryByUrl` | `thordata.tools.code` | url |  |

## Group: `ecommerce`

| spider_id | spider_name | key | class | module | params | type |
|-----------|------------|-----|-------|--------|--------|------|
| `amazon_comment_by-url` | `amazon.com` | `ecommerce.amazon_comment_by-url` | `Review` | `thordata.tools.ecommerce` | url, page_turning |  |
| `amazon_global-product_by-category-url` | `amazon.com` | `ecommerce.amazon_global-product_by-category-url` | `GlobalProductByCategoryUrl` | `thordata.tools.ecommerce` | url, sort_by, get_sponsored, maximum |  |
| `amazon_global-product_by-keywords` | `amazon.com` | `ecommerce.amazon_global-product_by-keywords` | `GlobalProductByKeywords` | `thordata.tools.ecommerce` | keyword, domain, lowest_price, highest_price, page_turning |  |
| `amazon_global-product_by-keywords-brand` | `amazon.com` | `ecommerce.amazon_global-product_by-keywords-brand` | `GlobalProductByKeywordsBrand` | `thordata.tools.ecommerce` | keyword, brands, page_turning |  |
| `amazon_global-product_by-seller-url` | `amazon.com` | `ecommerce.amazon_global-product_by-seller-url` | `GlobalProductBySellerUrl` | `thordata.tools.ecommerce` | url, maximum |  |
| `amazon_global-product_by-url` | `amazon.com` | `ecommerce.amazon_global-product_by-url` | `GlobalProductByUrl` | `thordata.tools.ecommerce` | url |  |
| `amazon_global-product_by-url` | `amazon.com` | `ecommerce.amazon_global-product_by-url` | `GlobalProductByUrl` | `thordata.tools.ecommerce` | url |  |
| `amazon_product-list_by-keywords-domain` | `amazon.com` | `ecommerce.amazon_product-list_by-keywords-domain` | `Search` | `thordata.tools.ecommerce` | keyword, domain, page_turning |  |
| `amazon_product_by-asin` | `amazon.com` | `ecommerce.amazon_product_by-asin` | `ProductByAsin` | `thordata.tools.ecommerce` | asin, domain |  |
| `amazon_product_by-asin` | `amazon.com` | `ecommerce.amazon_product_by-asin` | `ProductByAsin` | `thordata.tools.ecommerce` | asin, domain |  |
| `amazon_product_by-best-sellers` | `amazon.com` | `ecommerce.amazon_product_by-best-sellers` | `ProductByBestSellers` | `thordata.tools.ecommerce` | url, page_turning |  |
| `amazon_product_by-category-url` | `amazon.com` | `ecommerce.amazon_product_by-category-url` | `ProductByCategoryUrl` | `thordata.tools.ecommerce` | url, sort_by, page_turning |  |
| `amazon_product_by-keywords` | `amazon.com` | `ecommerce.amazon_product_by-keywords` | `ProductByKeywords` | `thordata.tools.ecommerce` | keyword, page_turning, lowest_price, highest_price |  |
| `amazon_product_by-url` | `amazon.com` | `ecommerce.amazon_product_by-url` | `ProductByUrl` | `thordata.tools.ecommerce` | url, zip_code |  |
| `amazon_seller_by-url` | `amazon.com` | `ecommerce.amazon_seller_by-url` | `Seller` | `thordata.tools.ecommerce` | url |  |
| `ebay_ebay_by-category-url` | `ebay.com` | `ecommerce.ebay_ebay_by-category-url` | `ProductByCategoryUrl` | `thordata.tools.ecommerce` | url, count |  |
| `ebay_ebay_by-keywords` | `ebay.com` | `ecommerce.ebay_ebay_by-keywords` | `ProductByKeywords` | `thordata.tools.ecommerce` | keywords, count |  |
| `ebay_ebay_by-listurl` | `ebay.com` | `ecommerce.ebay_ebay_by-listurl` | `ProductByListUrl` | `thordata.tools.ecommerce` | url, count |  |
| `ebay_ebay_by-url` | `ebay.com` | `ecommerce.ebay_ebay_by-url` | `ProductByUrl` | `thordata.tools.ecommerce` | url |  |
| `walmart_product_by-category-url` | `walmart.com` | `ecommerce.walmart_product_by-category-url` | `ProductByCategoryUrl` | `thordata.tools.ecommerce` | category_url, all_variations, page_turning |  |
| `walmart_product_by-keywords` | `walmart.com` | `ecommerce.walmart_product_by-keywords` | `ProductByKeywords` | `thordata.tools.ecommerce` | keyword, domain, all_variations, page_turning |  |
| `walmart_product_by-sku` | `walmart.com` | `ecommerce.walmart_product_by-sku` | `ProductBySku` | `thordata.tools.ecommerce` | sku, all_variations |  |
| `walmart_product_by-url` | `walmart.com` | `ecommerce.walmart_product_by-url` | `ProductByUrl` | `thordata.tools.ecommerce` | url, all_variations |  |
| `walmart_product_by-zipcodes` | `walmart.com` | `ecommerce.walmart_product_by-zipcodes` | `ProductByZipcodes` | `thordata.tools.ecommerce` | url, zip_code |  |

## Group: `professional`

| spider_id | spider_name | key | class | module | params | type |
|-----------|------------|-----|-------|--------|--------|------|
| `crunchbase_company_by-keywords` | `crunchbase.com` | `professional.crunchbase_company_by-keywords` | `CompanyByKeywords` | `thordata.tools.professional` | keyword |  |
| `crunchbase_company_by-url` | `crunchbase.com` | `professional.crunchbase_company_by-url` | `CompanyByUrl` | `thordata.tools.professional` | url |  |
| `glassdoor_company_by-inputfilter` | `glassdoor.com` | `professional.glassdoor_company_by-inputfilter` | `CompanyByInputFilter` | `thordata.tools.professional` | company_name, location, industries, Job_title |  |
| `glassdoor_company_by-keywords` | `glassdoor.com` | `professional.glassdoor_company_by-keywords` | `CompanyByKeywords` | `thordata.tools.professional` | search_url, max_search_results |  |
| `glassdoor_company_by-listurl` | `glassdoor.com` | `professional.glassdoor_company_by-listurl` | `CompanyByListUrl` | `thordata.tools.professional` | url |  |
| `glassdoor_company_by-url` | `glassdoor.com` | `professional.glassdoor_company_by-url` | `CompanyByUrl` | `thordata.tools.professional` | url |  |
| `glassdoor_joblistings_by-keywords` | `glassdoor.com` | `professional.glassdoor_joblistings_by-keywords` | `JobByKeywords` | `thordata.tools.professional` | keyword, location, country |  |
| `glassdoor_joblistings_by-listurl` | `glassdoor.com` | `professional.glassdoor_joblistings_by-listurl` | `JobByListUrl` | `thordata.tools.professional` | url |  |
| `glassdoor_joblistings_by-url` | `glassdoor.com` | `professional.glassdoor_joblistings_by-url` | `JobByUrl` | `thordata.tools.professional` | url |  |
| `indeed_companies-info_by-company-list-url` | `indeed.com` | `professional.indeed_companies-info_by-company-list-url` | `CompanyByListUrl` | `thordata.tools.professional` | company_list_url |  |
| `indeed_companies-info_by-company-url` | `indeed.com` | `professional.indeed_companies-info_by-company-url` | `CompanyByUrl` | `thordata.tools.professional` | company_url |  |
| `indeed_companies-info_by-industry-and-state` | `indeed.com` | `professional.indeed_companies-info_by-industry-and-state` | `CompanyByIndustryAndState` | `thordata.tools.professional` | industry, state |  |
| `indeed_companies-info_by-keyword` | `indeed.com` | `professional.indeed_companies-info_by-keyword` | `CompanyByKeyword` | `thordata.tools.professional` | keyword |  |
| `indeed_job-listings_by-job-url` | `indeed.com` | `professional.indeed_job-listings_by-job-url` | `JobByUrl` | `thordata.tools.professional` | job_url |  |
| `indeed_job-listings_by-keyword` | `indeed.com` | `professional.indeed_job-listings_by-keyword` | `JobByKeyword` | `thordata.tools.professional` | keyword, location, country, domain, date_posted, posted_by, pay, location_radius |  |

## Group: `search`

| spider_id | spider_name | key | class | module | params | type |
|-----------|------------|-----|-------|--------|--------|------|
| `google-play-store_information_by-url` | `google.com` | `search.google-play-store_information_by-url` | `AppInfo` | `thordata.tools.search` | app_url, country |  |
| `google-play-store_reviews_by-url` | `google.com` | `search.google-play-store_reviews_by-url` | `Reviews` | `thordata.tools.search` | app_url, num_of_reviews, start_date, end_date, country |  |
| `google_comment_by-url` | `google.com` | `search.google_comment_by-url` | `Reviews` | `thordata.tools.search` | url, days_limit |  |
| `google_map-details_by-cid` | `google.com` | `search.google_map-details_by-cid` | `DetailsByCid` | `thordata.tools.search` | CID |  |
| `google_map-details_by-location` | `google.com` | `search.google_map-details_by-location` | `DetailsByLocation` | `thordata.tools.search` | country, keyword, lat, long, zoom_level |  |
| `google_map-details_by-placeid` | `google.com` | `search.google_map-details_by-placeid` | `DetailsByPlaceId` | `thordata.tools.search` | place_id |  |
| `google_map-details_by-url` | `google.com` | `search.google_map-details_by-url` | `DetailsByUrl` | `thordata.tools.search` | url |  |
| `google_map-details_by-url` | `google.com` | `search.google_map-details_by-url` | `DetailsByUrl` | `thordata.tools.search` | url |  |
| `google_shopping_by-keywords` | `google.com` | `search.google_shopping_by-keywords` | `ProductByKeywords` | `thordata.tools.search` | keyword, country |  |
| `google_shopping_by-url` | `google.com` | `search.google_shopping_by-url` | `Product` | `thordata.tools.search` | url, country |  |

## Group: `social`

| spider_id | spider_name | key | class | module | params | type |
|-----------|------------|-----|-------|--------|--------|------|
| `facebook_comment_by-comments-url` | `facebook.com` | `social.facebook_comment_by-comments-url` | `Comment` | `thordata.tools.social` | url, get_all_replies, limit_records, comments_sort |  |
| `facebook_event_by-eventlist-url` | `facebook.com` | `social.facebook_event_by-eventlist-url` | `EventByEventListUrl` | `thordata.tools.social` | url, upcoming_events_only |  |
| `facebook_event_by-events-url` | `facebook.com` | `social.facebook_event_by-events-url` | `EventByEventsUrl` | `thordata.tools.social` | url |  |
| `facebook_event_by-search-url` | `facebook.com` | `social.facebook_event_by-search-url` | `EventBySearchUrl` | `thordata.tools.social` | url |  |
| `facebook_post_by-keywords` | `facebook.com` | `social.facebook_post_by-keywords` | `Posts` | `thordata.tools.social` | keyword, recent_posts, date, number |  |
| `facebook_post_by-posts-url` | `facebook.com` | `social.facebook_post_by-posts-url` | `PostDetails` | `thordata.tools.social` | url |  |
| `facebook_profile_by-profiles-url` | `facebook.com` | `social.facebook_profile_by-profiles-url` | `Profile` | `thordata.tools.social` | url |  |
| `ins_allreel_by-url` | `instagram.com` | `social.ins_allreel_by-url` | `AllReel` | `thordata.tools.social` | url, num_of_posts, posts_to_not_include, start_date, end_date |  |
| `ins_comment_by-posturl` | `instagram.com` | `social.ins_comment_by-posturl` | `Comment` | `thordata.tools.social` | posturl |  |
| `ins_posts_by-posturl` | `instagram.com` | `social.ins_posts_by-posturl` | `PostByUrl` | `thordata.tools.social` | posturl |  |
| `ins_posts_by-profileurl` | `instagram.com` | `social.ins_posts_by-profileurl` | `Post` | `thordata.tools.social` | profileurl, resultsLimit, start_date, end_date, post_type |  |
| `ins_profiles_by-profileurl` | `instagram.com` | `social.ins_profiles_by-profileurl` | `ProfileByUrl` | `thordata.tools.social` | profileurl |  |
| `ins_profiles_by-username` | `instagram.com` | `social.ins_profiles_by-username` | `Profile` | `thordata.tools.social` | username |  |
| `ins_reel_by-listurl` | `instagram.com` | `social.ins_reel_by-listurl` | `ReelByListUrl` | `thordata.tools.social` | url, num_of_posts, posts_to_not_include, start_date, end_date |  |
| `ins_reel_by-url` | `instagram.com` | `social.ins_reel_by-url` | `Reel` | `thordata.tools.social` | url |  |
| `linkedin_company_information_by-url` | `linkedin.com` | `social.linkedin_company_information_by-url` | `Company` | `thordata.tools.social` | url |  |
| `linkedin_job_listings_information_by-job-listing-url` | `linkedin.com` | `social.linkedin_job_listings_information_by-job-listing-url` | `Jobs` | `thordata.tools.social` | job_listing_url, page_turning |  |
| `linkedin_job_listings_information_by-job-url` | `linkedin.com` | `social.linkedin_job_listings_information_by-job-url` | `JobByUrl` | `thordata.tools.social` | job_url |  |
| `linkedin_job_listings_information_by-keyword` | `linkedin.com` | `social.linkedin_job_listings_information_by-keyword` | `JobByKeyword` | `thordata.tools.social` | location, keyword, time_range, experience_level, job_type, remote, company, selective_search, jobs_to_not_include, location_radius, page_turning |  |
| `reddit_comment_by-url` | `reddit.com` | `social.reddit_comment_by-url` | `Comment` | `thordata.tools.social` | url, days_back, load_all_replies, comment_limit |  |
| `reddit_posts_by-keywords` | `reddit.com` | `social.reddit_posts_by-keywords` | `PostsByKeywords` | `thordata.tools.social` | keyword, date, num_of_posts, sort_by |  |
| `reddit_posts_by-subredditurl` | `reddit.com` | `social.reddit_posts_by-subredditurl` | `PostsBySubredditUrl` | `thordata.tools.social` | url, sort_by, num_of_posts, sort_by_time |  |
| `reddit_posts_by-url` | `reddit.com` | `social.reddit_posts_by-url` | `Posts` | `thordata.tools.social` | url |  |
| `tiktok_comment_by-url` | `tiktok.com` | `social.tiktok_comment_by-url` | `Comment` | `thordata.tools.social` | url, page_turning |  |
| `tiktok_posts_by-keywords` | `tiktok.com` | `social.tiktok_posts_by-keywords` | `PostsByKeywords` | `thordata.tools.social` | search_keyword, num_of_posts, posts_to_not_include, country |  |
| `tiktok_posts_by-listurl` | `tiktok.com` | `social.tiktok_posts_by-listurl` | `PostsByListUrl` | `thordata.tools.social` | url, num_of_posts |  |
| `tiktok_posts_by-profileurl` | `tiktok.com` | `social.tiktok_posts_by-profileurl` | `PostsByProfileUrl` | `thordata.tools.social` | url, start_date, end_date, num_of_posts, what_to_collect, post_type, posts_to_not_include, country |  |
| `tiktok_posts_by-url` | `tiktok.com` | `social.tiktok_posts_by-url` | `Post` | `thordata.tools.social` | url, country |  |
| `tiktok_profiles_by-listurl` | `tiktok.com` | `social.tiktok_profiles_by-listurl` | `ProfilesByListUrl` | `thordata.tools.social` | search_url, country, page_turning |  |
| `tiktok_profiles_by-url` | `tiktok.com` | `social.tiktok_profiles_by-url` | `Profile` | `thordata.tools.social` | url, country |  |
| `tiktok_shop_by-category-url` | `tiktok.com` | `social.tiktok_shop_by-category-url` | `ShopByCategoryUrl` | `thordata.tools.social` | category_url |  |
| `tiktok_shop_by-keywords` | `tiktok.com` | `social.tiktok_shop_by-keywords` | `ShopByKeywords` | `thordata.tools.social` | keyword, domain, page_turning |  |
| `tiktok_shop_by-url` | `tiktok.com` | `social.tiktok_shop_by-url` | `Shop` | `thordata.tools.social` | url |  |
| `twitter_post_by-posturl` | `x.com` | `social.twitter_post_by-posturl` | `Post` | `thordata.tools.social` | url |  |
| `twitter_post_by-profileurl` | `x.com` | `social.twitter_post_by-profileurl` | `PostByProfileUrl` | `thordata.tools.social` | url |  |
| `twitter_profile_by-profileurl` | `x.com` | `social.twitter_profile_by-profileurl` | `Profile` | `thordata.tools.social` | url |  |
| `twitter_profile_by-username` | `x.com` | `social.twitter_profile_by-username` | `ProfileByUsername` | `thordata.tools.social` | user_name |  |

## Group: `travel`

| spider_id | spider_name | key | class | module | params | type |
|-----------|------------|-----|-------|--------|--------|------|
| `airbnb_product_by-location` | `airbnb.com` | `travel.airbnb_product_by-location` | `ProductByLocation` | `thordata.tools.travel` | location, check_in, check_out, num_of_adults, num_of_children, num_of_infants, num_of_pets, country, currency |  |
| `airbnb_product_by-searchurl` | `airbnb.com` | `travel.airbnb_product_by-searchurl` | `ProductBySearchUrl` | `thordata.tools.travel` | searchurl, country |  |
| `airbnb_product_by-url` | `airbnb.com` | `travel.airbnb_product_by-url` | `ProductByUrl` | `thordata.tools.travel` | url, country |  |
| `booking_hotellist_by-url` | `booking.com` | `travel.booking_hotellist_by-url` | `HotelByUrl` | `thordata.tools.travel` | url |  |
| `zillow_price_by-url` | `zillow.com` | `travel.zillow_price_by-url` | `PriceByUrl` | `thordata.tools.travel` | url |  |
| `zillow_product_by-filter` | `zillow.com` | `travel.zillow_product_by-filter` | `ProductByFilter` | `thordata.tools.travel` | keywords_location, listingCategory, HomeType, days_on_zillow, maximum |  |
| `zillow_product_by-listurl` | `zillow.com` | `travel.zillow_product_by-listurl` | `ProductByListUrl` | `thordata.tools.travel` | url, maximum |  |
| `zillow_product_by-url` | `zillow.com` | `travel.zillow_product_by-url` | `ProductByUrl` | `thordata.tools.travel` | url |  |

## Group: `video`

| spider_id | spider_name | key | class | module | params | type |
|-----------|------------|-----|-------|--------|--------|------|
| `youtube_audio_by-url` | `youtube.com` | `video.youtube_audio_by-url` | `AudioDownload` | `thordata.tools.video` | url | video |
| `youtube_comment_by-id` | `youtube.com` | `video.youtube_comment_by-id` | `Comments` | `thordata.tools.video` | video_id, num_of_comments, sort_by | video |
| `youtube_product_by-id` | `youtube.com` | `video.youtube_product_by-id` | `VideoInfo` | `thordata.tools.video` | video_id | video |
| `youtube_profiles_by-keyword` | `youtube.com` | `video.youtube_profiles_by-keyword` | `Profile` | `thordata.tools.video` | keyword, page_turning | video |
| `youtube_profiles_by-url` | `youtube.com` | `video.youtube_profiles_by-url` | `ProfileByUrl` | `thordata.tools.video` | url | video |
| `youtube_transcript_by-id` | `youtube.com` | `video.youtube_transcript_by-id` | `SubtitleDownload` | `thordata.tools.video` | video_id, subtitles_type | video |
| `youtube_video-post_by-explore` | `youtube.com` | `video.youtube_video-post_by-explore` | `VideoPostByExplore` | `thordata.tools.video` | url, all_tabs |  |
| `youtube_video-post_by-hashtag` | `youtube.com` | `video.youtube_video-post_by-hashtag` | `VideoPostByHashtag` | `thordata.tools.video` | hashtag, num_of_posts |  |
| `youtube_video-post_by-keyword` | `youtube.com` | `video.youtube_video-post_by-keyword` | `VideoPostByKeyword` | `thordata.tools.video` | keyword, num_of_posts |  |
| `youtube_video-post_by-podcast-url` | `youtube.com` | `video.youtube_video-post_by-podcast-url` | `VideoPostByPodcastUrl` | `thordata.tools.video` | url, num_of_posts |  |
| `youtube_video-post_by-search-filters` | `youtube.com` | `video.youtube_video-post_by-search-filters` | `VideoPostBySearchFilters` | `thordata.tools.video` | keyword_search, features, type, duration, upload_date, num_of_posts |  |
| `youtube_video-post_by-url` | `youtube.com` | `video.youtube_video-post_by-url` | `VideoPostByUrl` | `thordata.tools.video` | url, order_by, start_index, num_of_posts |  |
| `youtube_video_by-url` | `youtube.com` | `video.youtube_video_by-url` | `VideoDownload` | `thordata.tools.video` | url | video |