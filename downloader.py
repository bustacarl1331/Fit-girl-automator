import logging
import requests
import os
from bs4 import BeautifulSoup
from tqdm import tqdm
import time
from playwright.sync_api import sync_playwright

# Setup logging to file

logging.basicConfig(
    filename='app_debug.log', 
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='w'
)

def log_debug(msg):
    print(msg)
    logging.debug(msg)

class FitGirlDownloader:
    def __init__(self, game_url):
        log_debug(f"Initializing Downloader for: {game_url}")
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

    def start_engine(self):
        """Starts the global Playwright engine if not running."""
        try:
            # Check if we need to initialize (if either mismatch)
            needs_init = False
            if not hasattr(self, 'playwright') or self.playwright is None:
                needs_init = True
            elif not hasattr(self, 'browser') or self.browser is None:
                 needs_init = True
            
            if needs_init:
                log_debug("Starting Playwright Engine...")
                # Cleanup potential partial state
                if hasattr(self, 'playwright') and self.playwright:
                    try: self.playwright.stop()
                    except: pass
                self.playwright = None
                
                self.playwright = sync_playwright().start()
                
                log_debug("Launching Chromium...")
                # Try headless=True by default for stability, user can use debug build for visible
                # If we are in debug mode (checking env var or similar? No, just hardcode for now)
                # Let's stick to HEADLESS=TRUE for the release.
                self.browser = self.playwright.chromium.launch(headless=True)
                log_debug("Browser Launched Successfully.")
                
        except Exception as e:
            log_debug(f"CRITICAL: Failed to start engine: {e}")
            # Clean up so we retry next time instead of partial broken state
            self.playwright = None
            self.browser = None
            raise e
            
    def close_engine(self):
        """Closes the global Playwright engine."""
        try:
            if hasattr(self, 'browser') and self.browser:
                self.browser.close()
                self.browser = None
            if hasattr(self, 'playwright') and self.playwright:
                self.playwright.stop()
                self.playwright = None
                log_debug("Playwright Engine Stopped.")
        except Exception as e:
            log_debug(f"Error closing engine: {e}")

    def resolve_single_link_playwright(self, url):
        log_debug(f"Resolving: {url}")
        try:
            self.start_engine() # Ensure browser is running
        except Exception as e:
            log_debug(f"Engine start failed: {e}")
            return None
        
        page = None
        final_url = None
        try:
            page = self.browser.new_page()
            log_debug("Page created. Navigating...")
            
            # Use domcontentloaded to avoid waiting for heavy ads
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            log_debug("Navigation complete (domcontentloaded).")
            
            # Check if we are on fuckingfast
            if "fuckingfast" not in page.url and "fitgirl" not in page.url:
                 log_debug(f"Redirected to unexpected URL: {page.url}")

            # Popup handling
            try:
                # Wait for button to be visible first
                log_debug("Waiting for DOWNLOAD button...")
                page.wait_for_selector(".link-button, button:has-text('DOWNLOAD')", state="visible", timeout=15000)
                
                with page.expect_popup(timeout=5000) as popup_info:
                    log_debug("Attempting to click DOWNLOAD (Popup trigger)...")
                    page.click(".link-button, button:has-text('DOWNLOAD')", timeout=5000)
                popup = popup_info.value
                popup.close()
                log_debug("Popup handled.")
                time.sleep(1)
            except Exception:
                log_debug("No popup trigger found or timed out (normal).")
            
            # Real Download
            try:
                # Ensure button is still there
                page.wait_for_selector(".link-button, button:has-text('DOWNLOAD')", state="visible", timeout=10000)
                
                with page.expect_download(timeout=45000) as download_info:
                    # sometimes the button selector might be tricky, try generic
                    log_debug("Attempting to click DOWNLOAD (Real)...")
                    page.click(".link-button, button:has-text('DOWNLOAD')", timeout=10000)
                
                download = download_info.value
                final_url = download.url
                log_debug(f"Download URL captured: {final_url}")
                download.cancel()
            except Exception as e:
                 log_debug(f" -> Download click not found or timeout: {e}")

        except Exception as e:
            log_debug(f"Resolution failed with exception: {e}")
        finally:
            if page:
                try:
                    page.close() # Ensure page is always closed
                except:
                    pass
        
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

