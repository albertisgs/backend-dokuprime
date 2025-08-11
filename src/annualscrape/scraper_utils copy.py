# src/annualscrape/scraper_utils.py

import aiohttp
import asyncio
import os
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote, urlparse, parse_qs

# === Helper Functions ===
def extract_year(text: str):
    """Extracts the last 4-digit year from a string."""
    print(f"Processing text: '{text}'")
    matches = re.findall(r'(20\d{2})', text)
    return int(matches[-1]) if matches else None

async def get_google_drive_filename(session: aiohttp.ClientSession, file_id: str) -> str:
    """Gets the original filename from a Google Drive link."""
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

# === Download Functions ===
async def download_file_async(session: aiohttp.ClientSession, url: str, filepath: str, is_google_drive: bool = False) -> bool:
    """Asynchronously downloads a file, handling Google Drive complexities."""
    try:
        download_url = url
        if is_google_drive:
            file_id_match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
            if not file_id_match:
                return False
            file_id = file_id_match.group(1)
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        # We make a request and follow redirects to get the final file
        async with session.get(download_url, allow_redirects=True) as response:
            if response.status == 200 and 'application' in response.headers.get('content-type', ''):
                with open(filepath, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                # Verify file is not an error page
                if os.path.getsize(filepath) < 1000:
                     with open(filepath, 'r', encoding='utf-8', errors='ignore') as f_check:
                        if '<html' in f_check.read(200).lower():
                            os.remove(filepath)
                            return False
                return True
            else:
                # Handle Google Drive's virus scan warning page
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
    except Exception as e:
        print(f"Error downloading {url}: {e}") # Log errors to server console
    return False


# === Main Scraping Logic ===
async def process_company_async(session: aiohttp.ClientSession, company_name: str, config: dict, base_download_dir: str):
    """Processes a single company to find and download annual reports."""
    logs = []
    output_dir = os.path.join(base_download_dir, company_name.upper())
    os.makedirs(output_dir, exist_ok=True)
    
    logs.append(f"Processing {company_name.upper()}. Saving to: {output_dir}")

    try:
        async with session.get(config['page_url']) as response:
            if response.status != 200:
                logs.append(f"ERROR: Failed to fetch page for {company_name}. Status: {response.status}")
                return logs
            html = await response.text()

        soup = BeautifulSoup(html, 'html.parser')
        tasks = []
        
        start_year = config.get("start_year", 2020)
        end_year = config.get("end_year", 2024)

        if config.get("is_google_drive"):
            links = soup.find_all('a', href=re.compile(r'drive\.google\.com/file/d/'))
            for link in links:
                href = link['href']
                file_id_match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', href)
                if file_id_match:
                    file_id = file_id_match.group(1)
                    filename = await get_google_drive_filename(session, file_id)
                    year = extract_year(filename)
                    if year and start_year <= year <= end_year:
                        filepath = os.path.join(output_dir, filename)
                        if not os.path.exists(filepath):
                            tasks.append({'url': href, 'path': filepath, 'is_gdrive': True, 'name': filename})
                        else:
                            logs.append(f"SKIPPED: '{filename}' already exists.")
        else: # WIKA / WASKITA logic
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
        
        semaphore = asyncio.Semaphore(5) # Limit to 5 concurrent downloads
        
        async def download_with_semaphore(task):
            async with semaphore:
                success = await download_file_async(session, task['url'], task['path'], task['is_gdrive'])
                if success:
                    logs.append(f"SUCCESS: Downloaded '{task['name']}'.")
                else:
                    logs.append(f"FAILED: Could not download '{task['name']}'.")
        
        await asyncio.gather(*(download_with_semaphore(task) for task in tasks))

    except Exception as e:
        logs.append(f"CRITICAL ERROR processing {company_name}: {e}")
    
    return logs