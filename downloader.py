import os
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import time
from playwright.sync_api import sync_playwright

class FitGirlDownloader:
    def __init__(self, game_url):
        self.game_url = game_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def fetch_files_info(self):
        """
        Fetches the list of available files without downloading them.
        Returns a list of dicts: {'url': str, 'name': str, 'is_optional': bool}
        """
        print(f"Fetching game page: {self.game_url}")
        try:
            response = self.session.get(self.game_url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching game page: {e}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        
        target_spoiler = None
        spoilers = soup.find_all('div', class_='su-spoiler')
        
        for spoiler in spoilers:
            content_div = spoiler.find('div', class_='su-spoiler-content')
            if content_div:
                links = content_div.find_all('a')
                for link in links:
                    if 'fuckingfast.co' in link.get('href', ''):
                        target_spoiler = content_div
                        break
            if target_spoiler:
                break
        
        if not target_spoiler:
            return []

        files_info = []
        links = target_spoiler.find_all('a')
        
        # Heuristic for sequential naming if needed
        part_counter = 1
        
        for a in links:
            href = a.get('href')
            if href and 'fuckingfast.co' in href:
                # Attempt to guess name from text
                text_content = a.get_text(strip=True)
                
                # Determine classification
                text_lower = text_content.lower()
                href_lower = href.lower()
                
                # Logic:
                # Selective often has "fg-selective-" in name
                # Optional often has "fg-optional-" in name
                
                if "fg-selective-" in text_lower or "selective" in text_lower:
                    file_type = "selective"
                    display_name = text_content
                elif "fg-optional-" in text_lower or "optional" in text_lower:
                    file_type = "optional"
                    display_name = text_content
                else:
                    file_type = "core"
                    if "part" in text_lower and ".rar" in text_lower:
                        display_name = text_content
                    else:
                        display_name = f"part{part_counter:03d}.rar"
                        # Only increment counter for core/numbered parts to avoid gaps?
                        # Actually FitGirl parts are usually the only ones numbered part01-partXX. 
                        # Selective/Optional have full names.
                
                if file_type == "core":
                    part_counter += 1

                files_info.append({
                    "url": href,
                    "name": display_name,
                    "type": file_type, # core, selective, optional
                    "original_text": text_content
                })

                
        return files_info

    def resolve_single_link_playwright(self, url):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            final_url = None
            try:
                page.goto(url)
                
                # Popup handling
                try:
                    with page.expect_popup(timeout=2000) as popup_info:
                        page.click(".link-button, button:has-text('DOWNLOAD')", timeout=2000)
                    popup = popup_info.value
                    popup.close()
                    time.sleep(1)
                except Exception:
                    pass
                
                # Real Download
                try:
                    with page.expect_download(timeout=15000) as download_info:
                        page.click(".link-button, button:has-text('DOWNLOAD')", timeout=5000)
                    
                    download = download_info.value
                    final_url = download.url
                    download.cancel()
                except Exception as e:
                     print(f" -> Download click failed: {e}")

            except Exception as e:
                print(f"Resolution failed: {e}")
            
            browser.close()
            return final_url

    def download_file(self, url, filename, progress_callback=None, check_cancel=None):
        """
        Downloads a file with resume support.
        progress_callback: function(downloaded_bytes, total_bytes)
        check_cancel: function() -> bool. If returns True, stop download.
        """
        if check_cancel and check_cancel():
            return False

        if os.path.exists(filename):
            existing_size = os.path.getsize(filename)
            headers = {'Range': f'bytes={existing_size}-'}
            mode = 'ab'
        else:
            existing_size = 0
            headers = {}
            mode = 'wb'

        try:
            # Add timeout (connect, read). 
            # Note: stream=True means read timeout applies to getting the headers, not the whole body.
            # For body, we rely on the socket timeout or iterator updates.
            response = self.session.get(url, stream=True, headers=headers, timeout=30)
            if response.status_code == 416: 
                if progress_callback:
                    # Report 100%
                    progress_callback(existing_size, existing_size)
                return True
                
            response.raise_for_status()
            
            if response.status_code == 200 and existing_size > 0:
                existing_size = 0
                mode = 'wb'

            total_size = int(response.headers.get('content-length', 0)) + existing_size
            
            block_size = 1024 * 1024
            current_size = existing_size
            
            with open(filename, mode) as f:
                # Iterate with a timeout protection is hard in pure requests without socket level hacks.
                # But typically 30s timeout on .get handles silent drops often for the initial connection.
                # For safety, we catch standard timeout exceptions.
                for data in response.iter_content(block_size):
                    if check_cancel and check_cancel():
                        return False
                        
                    f.write(data)
                    current_size += len(data)
                    
                    if progress_callback:
                        progress_callback(current_size, total_size)
                    
            return True
        except (requests.exceptions.RequestException, ConnectionError) as e:
            print(f"Download error (Network): {e}")
            return False
        except Exception as e:
            print(f"Download error (General): {e}")
            return False

