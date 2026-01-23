"""
YouTube Video Downloader Example
================================

Downloads video/audio from YouTube using Thordata's high-speed infrastructure.
"""

import os

from thordata import CommonSettings, ThordataClient
from thordata.tools import YouTube


def main():
    client = ThordataClient(
        scraper_token=os.getenv("THORDATA_SCRAPER_TOKEN"),
        public_token=os.getenv("THORDATA_PUBLIC_TOKEN"),
        public_key=os.getenv("THORDATA_PUBLIC_KEY"),
    )

    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    print(f"🎬 Processing Video: {video_url}")

    # Define Settings (Resolution, Format, etc.)
    settings = CommonSettings(
        resolution="720p", video_codec="vp9", is_subtitles="false"
    )

    # Create Request
    request = YouTube.VideoDownload(url=video_url, common_settings=settings)

    # Run
    task_id = client.run_tool(request)
    print(f"⏳ Task {task_id} is processing...")

    # Poll
    status = client.wait_for_task(task_id)

    if status == "finished":
        download_link = client.get_task_result(task_id)
        print(f"⬇️ Download Link: {download_link}")
    else:
        print(f"Failed: {status}")


if __name__ == "__main__":
    main()
