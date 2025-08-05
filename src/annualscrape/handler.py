
# src/annualscrape/handler.py

import os
import aiohttp
import asyncio
import random
from . import scraper_utils

class ScraperHandler:
    def __init__(self):
        self.base_download_dir = os.path.join(
            os.path.abspath(os.path.dirname(__file__)).rsplit("src", 1)[0],
            "downloads", "annual_reports"
        )
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        ]
        # --- UPDATED SOURCES CONFIGURATION ---
        self.sources = {
            "wika": {
                "scraper_type": "dynamic",
                "base_url": "https://investor.wika.co.id/",
                "page_url": "https://investor.wika.co.id/ar.html",
                "subfolder": "wika"
            },
            "waskita": {
                "scraper_type": "dynamic",
                "base_url": "https://investor.waskita.co.id/",
                "page_url": "https://investor.waskita.co.id/ar.html",
                "subfolder": "waskita"
            },
            "hutama": {
                "scraper_type": "direct",
                "subfolder": "hutama",
                "direct_links": [
                    "https://drive.google.com/file/d/1l-1icKeUPsIo5S2DcyowSS7OtaqF9pAW/view",
                    "https://drive.google.com/file/d/1BKJ7ULVU7JS0fYnsmzaQ6jhHr5pnB0bQ/view",
                    "https://drive.google.com/file/d/1LIc7QgKIjagwbAlMZK42r5hWOJJF_5lx/view",
                    "https://drive.google.com/file/d/1BPMpO6Gep8UHZPlscTC_tbr25V5TAJPJ/view",
                    "https://drive.google.com/file/d/1DQJpjyaihOsRfhGENdLQFnsAhOYLWGou/view"
                ]
            },
            "ptpp": {
                "scraper_type": "direct",
                "subfolder": "pp",
                "direct_links": [
                    "https://homepage.ptpp.co.id/storage/6837/PTPP---AR-2024---250408b.pdf",
                    "https://homepage.ptpp.co.id/storage/5402/PTPP-AR-2023.pdf",
                    "https://homepage.ptpp.co.id/storage/4795/ANNUAL-REPORT-PTPP-2022.pdf",
                    "https://homepage.ptpp.co.id/storage/4793/ANNUAL-REPORT-PTPP-2021.pdf",
                    "https://homepage.ptpp.co.id/storage/4791/ANNUAL-REPORT-PTPP-2020.pdf"
                ]
            }
        }
        print("ScraperHandler Initiated")

    # <<< MODIFICATION: New helper method to manage the dynamic scrapers and their session
    async def _run_dynamic_scrapers(self, dynamic_tasks_configs):
        """
        Creates a shared aiohttp session and runs all dynamic scraping tasks in parallel.
        """
        if not dynamic_tasks_configs:
            return []

        timeout = aiohttp.ClientTimeout(total=None, connect=15, sock_read=300)
        connector = aiohttp.TCPConnector(ssl=False, limit_per_host=10)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            dynamic_tasks = []
            for name, config in dynamic_tasks_configs:
                headers = {'User-Agent': random.choice(self.user_agents)}
                
                if config.get("scraper_type") == "dynamic_gdrive":
                    task = scraper_utils.process_company_dynamic_gdrive(
                        session, name, config, self.base_download_dir, headers
                    )
                else:
                    task = scraper_utils.process_company_dynamic(
                        session, name, config, self.base_download_dir, headers
                    )
                dynamic_tasks.append(task)
            
            # This gather runs Wika, Waskita, and Hutama in parallel with each other
            return await asyncio.gather(*dynamic_tasks)

   # <<< NEW METHOD: To run scraping for a single company >>>
    async def run_single_scrape(self, company_name: str):
        """
        Runs the scraping process for a single specified company.
        """
        print(f"Starting single scrape process for: {company_name.upper()}...")
        
        config = self.sources.get(company_name)
        if not config:
            print(f"ERROR: Configuration for '{company_name}' not found.")
            return

        scraper_type = config.get("scraper_type")
        results = []

        if scraper_type == "direct":
            # Direct scrapers can run standalone
            results = await scraper_utils.process_company_direct(company_name, config, self.base_download_dir)
        
        elif scraper_type in ["dynamic", "dynamic_gdrive"]:
            # Dynamic scrapers need an aiohttp session
            timeout = aiohttp.ClientTimeout(total=None, connect=15, sock_read=300)
            connector = aiohttp.TCPConnector(ssl=False, limit_per_host=10)
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                headers = {'User-Agent': random.choice(self.user_agents)}
                if scraper_type == "dynamic_gdrive":
                    results = await scraper_utils.process_company_dynamic_gdrive(
                        session, company_name, config, self.base_download_dir, headers
                    )
                else:
                    results = await scraper_utils.process_company_dynamic(
                        session, company_name, config, self.base_download_dir, headers
                    )
        else:
            print(f"ERROR: Unknown scraper_type '{scraper_type}' for company '{company_name}'.")
            return

        # Print logs for the single run
        if results:
            for log_entry in results:
                print(log_entry)
        
        print(f"Single scrape process for {company_name.upper()} finished.")

    async def run_full_scrape(self):
        # ... (run_full_scrape method remains unchanged)
        print("Starting full scrape process...")
        
        direct_tasks = []
        dynamic_tasks_configs = []
        for name, config in self.sources.items():
            if config.get("scraper_type") == "direct":
                task = scraper_utils.process_company_direct(name, config, self.base_download_dir)
                direct_tasks.append(task)
            elif config.get("scraper_type") in ["dynamic", "dynamic_gdrive"]:
                dynamic_tasks_configs.append((name, config))

        all_tasks = [
            self._run_dynamic_scrapers(dynamic_tasks_configs)
        ]
        
        all_tasks.extend(direct_tasks)

        print("Launching all company scrapers in parallel...")
        all_results_nested = await asyncio.gather(*all_tasks)

        all_results = []
        for result_group in all_results_nested:
            if result_group and isinstance(result_group[0], list):
                 for sublist in result_group:
                     all_results.append(sublist)
            else:
                 all_results.append(result_group)

        for log_list in all_results:
            if log_list:
                for log_entry in log_list:
                    print(log_entry)
        
        print("Full scrape process finished.")