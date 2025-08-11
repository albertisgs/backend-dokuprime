# src/annualscrape/handler.py

import os
import aiohttp
import asyncio
from . import scraper_utils

class ScraperHandler:
    def __init__(self):
        # Base directory for all downloads, relative to the project root
        self.base_download_dir = os.path.join(
            os.path.abspath(os.path.dirname(__file__)).rsplit("src", 1)[0],
            "downloads", "annual_reports"
        )
        # Scraping configuration
        self.sources = {
            "hutama": {
                "base_url": "https://www.hutamakarya.com/",
                "page_url": "https://www.hutamakarya.com/en/annual-report",
                "is_google_drive": True,
            },
            "wika": {
                "base_url": "https://investor.wika.co.id/",
                "page_url": "https://investor.wika.co.id/ar.html",
                "is_google_drive": False,
            },
            "waskita": {
                "base_url": "https://investor.waskita.co.id/",
                "page_url": "https://investor.waskita.co.id/ar.html",
                "is_google_drive": False,
            }
        }
        print("ScraperHandler Initiated")

    async def run_full_scrape(self):
        """
        Runs the full scraping process for all configured sources.
        This function is designed to be run as a background task.
        """
        print("Starting full scrape process...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        connector = aiohttp.TCPConnector(ssl=False, limit_per_host=5)
        
        async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
            tasks = [
                scraper_utils.process_company_async(session, name, config, self.base_download_dir)
                for name, config in self.sources.items()
            ]
            results = await asyncio.gather(*tasks)
            
            # The results are lists of log strings. We can print them to the server console.
            for log_list in results:
                for log_entry in log_list:
                    print(log_entry)
        
        print("Full scrape process finished.")