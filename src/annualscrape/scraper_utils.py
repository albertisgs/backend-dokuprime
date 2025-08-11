
# src/annualscrape/scraper_utils.py

import aiohttp
import httpx  # New import
import aiofiles # New import
import asyncio
import os
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote, urlparse, parse_qs

# ==============================================================================
# SECTION 1: DYNAMIC SCRAPING LOGIC (for WIKA, WASKITA)
# This uses aiohttp to find links on a page.
# ==============================================================================

def extract_year(text: str):
    """Extracts the last 4-digit year (2020 and newer) from a string."""
    matches = re.findall(r'(20[2-9]\d)', text)
    return int(matches[-1]) if matches else None

async def get_google_drive_filename(session: aiohttp.ClientSession, file_id: str) -> str:
    # ... (This function remains unchanged)
    try:
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        async with session.get(url, allow_redirects=False) as response:
            if 'content-disposition' in response.headers:
                content = response.headers['content-disposition']
                filename_match = re.findall(r'filename="(.+)"', content)
                if filename_match:
                    return filename_match[0]
    except Exception:
        pass
    return f"annual_report_{file_id}.pdf"


async def download_file_dynamic(session: aiohttp.ClientSession, url: str, filepath: str, is_google_drive: bool = False) -> bool:
    # ... (This function, formerly download_file_async, remains unchanged)
    try:
        download_url = url
        if is_google_drive:
            file_id_match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
            if not file_id_match: return False
            file_id = file_id_match.group(1)
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        async with session.get(download_url, allow_redirects=True) as response:
            if response.status == 200 and 'application' in response.headers.get('content-type', ''):
                with open(filepath, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                if os.path.getsize(filepath) < 1000:
                     with open(filepath, 'r', encoding='utf-8', errors='ignore') as f_check:
                        if '<html' in f_check.read(200).lower():
                            os.remove(filepath)
                            return False
                return True
            else:
                content = await response.text()
                confirm_match = re.search(r'confirm=([a-zA-Z0-9_-]+)', content)
                if confirm_match:
                    confirm_token = confirm_match.group(1)
                    final_url = f"{download_url}&confirm={confirm_token}"
                    async with session.get(final_url) as final_response:
                        if final_response.status == 200:
                             with open(filepath, 'wb') as f:
                                async for chunk in final_response.content.iter_chunked(8192):
                                    f.write(chunk)
                             return True
    except Exception:
        pass
    return False


async def process_company_dynamic(session: aiohttp.ClientSession, company_name: str, config: dict, base_download_dir: str, headers: dict):
    # ... (This function, formerly process_company_async, remains unchanged)
    logs = []
    output_dir = os.path.join(base_download_dir, config["subfolder"])
    os.makedirs(output_dir, exist_ok=True)
    
    logs.append(f"Processing {company_name.upper()} with User-Agent: {headers.get('User-Agent')}")

    try:
        async with session.get(config['page_url'], headers=headers) as response:
            if response.status != 200:
                logs.append(f"ERROR: Failed to fetch page for {company_name}. Status: {response.status}")
                return logs
            html = await response.text()

        soup = BeautifulSoup(html, 'html.parser')
        tasks = []
        
        start_year = config.get("start_year", 2020)
        end_year = config.get("end_year", 2025)

        links = soup.find_all('a', href=re.compile(r"tracker\.pl.*redirect=.*\.pdf"))
        for link in links:
            full_url = urljoin(config["base_url"], link['href'])
            pdf_url = parse_qs(urlparse(full_url).query).get('redirect', [None])[0]
            if pdf_url:
                filename = unquote(pdf_url.split('/')[-1])
                year = extract_year(filename)
                if year and start_year <= year <= end_year:
                    filepath = os.path.join(output_dir, filename)
                    if not os.path.exists(filepath):
                        tasks.append({'url': pdf_url, 'path': filepath, 'is_gdrive': False, 'name': filename})
                    else:
                        logs.append(f"SKIPPED: '{filename}' already exists.")

        if not tasks:
            logs.append("No new files to download.")
            return logs

        logs.append(f"Found {len(tasks)} new file(s) to download.")
        
        semaphore = asyncio.Semaphore(5)
        
        async def download_with_semaphore(task):
            async with semaphore:
                success = await download_file_dynamic(session, task['url'], task['path'], task['is_gdrive'])
                if success:
                    logs.append(f"SUCCESS: Downloaded '{task['name']}'.")
                else:
                    logs.append(f"FAILED: Could not download '{task['name']}'.")
        
        await asyncio.gather(*(download_with_semaphore(task) for task in tasks))

    except Exception as e:
        logs.append(f"CRITICAL ERROR processing {company_name}: {e}")
    
    return logs


# ==============================================================================
# SECTION 2: DIRECT DOWNLOAD LOGIC (for HUTAMA, PTPP)
# This uses httpx and a predefined list of URLs.
# ==============================================================================

async def download_file_direct(client: httpx.AsyncClient, url: str, filepath: str, semaphore: asyncio.Semaphore):
    """Downloads a file from a direct URL using httpx."""
    async with semaphore:
        try:
            download_url = url
            if "drive.google.com" in url:
                file_id_match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
                if file_id_match:
                    file_id = file_id_match.group(1)
                    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"

            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124"}
            async with client.stream("GET", download_url, timeout=60, headers=headers, follow_redirects=True) as response:
                response.raise_for_status()
                
                filename = url.split("/")[-1]
                if "content-disposition" in response.headers:
                    disposition = response.headers["content-disposition"]
                    filename_match = re.search(r'filename="?([^"]+)"?', disposition)
                    if filename_match:
                        filename = filename_match.group(1)
                
                final_filepath = os.path.join(os.path.dirname(filepath), filename)

                if os.path.exists(final_filepath):
                    return f"SKIPPED: '{filename}' already exists."

                async with aiofiles.open(final_filepath, "wb") as f:
                    async for chunk in response.aiter_bytes():
                        await f.write(chunk)
                return f"SUCCESS: Downloaded '{filename}'."

        except Exception as e:
            return f"FAILED: Could not download {url}. Reason: {e}"


async def process_company_direct(company_name: str, config: dict, base_download_dir: str):
    """Processes a company by downloading files from a direct_links list."""
    logs = []
    output_dir = os.path.join(base_download_dir, config["subfolder"])
    os.makedirs(output_dir, exist_ok=True)
    
    logs.append(f"Processing {company_name.upper()} using direct links.")
    
    pdf_urls = config.get("direct_links", [])
    if not pdf_urls:
        logs.append("No direct links configured.")
        return logs

    logs.append(f"Found {len(pdf_urls)} direct link(s) to process.")
    
    semaphore = asyncio.Semaphore(5)  # Concurrency limit
    async with httpx.AsyncClient() as client:
        tasks = [
            download_file_direct(client, url, os.path.join(output_dir, "temp"), semaphore)
            for url in pdf_urls
        ]
        download_results = await asyncio.gather(*tasks)
    
    logs.extend(download_results)
    return logs