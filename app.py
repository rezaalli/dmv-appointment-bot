# app.py
import time
import os
import logging
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
DMV_START_URL = "https://www.dmv.ca.gov/portal/appointments/select-appointment-type"
ZIP_CODE = "92108"
LOCATION_SELECTOR = "//button[contains(text(), 'Select Location')]"
NO_DATES_AVAILABLE_TEXT = "Sorry, no dates available"
MAX_RETRIES = 3
PROXY_LIST = [
    "http://proxy1.example.com:8000",
    "http://proxy2.example.com:8000",
    "http://proxy3.example.com:8000"
]

# --- Randomized User-Agent ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
]

# Track failed proxies
FAILED_PROXIES = {}

def is_proxy_alive(proxy):
    """Check if proxy is responding."""
    try:
        response = requests.get("https://www.dmv.ca.gov", proxies={"http": proxy, "https": proxy}, timeout=5)
        if response.status_code == 200:
            logger.info(f"✅ Proxy {proxy} is alive.")
            return True
        else:
            logger.warning(f"⚠️ Proxy {proxy} failed with status: {response.status_code}")
            return False
    except Exception as e:
        logger.warning(f"⚠️ Proxy {proxy} is not reachable. Error: {e}")
        return False

def get_random_proxy():
    """Select a working proxy."""
    for proxy in PROXY_LIST:
        if proxy not in FAILED_PROXIES or FAILED_PROXIES[proxy] < 3:
            if is_proxy_alive(proxy):
                return proxy
            else:
                FAILED_PROXIES[proxy] = FAILED_PROXIES.get(proxy, 0) + 1
    logger.error("💥 All proxies failed. Restarting proxy rotation...")
    FAILED_PROXIES.clear()
    time.sleep(60)
    return get_random_proxy()

def init_driver():
    logger.info("🌀 Initializing Chrome Driver")
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')

    # Fingerprint Evasion
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument(f'user-agent={random.choice(USER_AGENTS)}')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # Proxy Rotation
    proxy = get_random_proxy()
    logger.info(f"🌐 Using Proxy: {proxy}")
    options.add_argument(f'--proxy-server={proxy}')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # More Anti-detection
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    driver.set_page_load_timeout(30)
    return driver

def main():
    retry_count = 0
    while True:
        try:
            if retry_count >= MAX_RETRIES:
                logger.error("💥 Maximum retries reached. Restarting with a new Proxy...")
                retry_count = 0
            logger.info("🚀 Starting Appointment Bot")
            driver = init_driver()
            driver.get(DMV_START_URL)

            logger.info("🌐 Navigated to DMV Page")
            
            # Check if navigation was successful
            if "select-appointment-type" not in driver.current_url:
                logger.info("✅ Successfully navigated.")
            else:
                logger.error("❌ Navigation failed, retrying with new proxy...")
                retry_count += 1
                driver.quit()
                continue
            
            # Other navigation steps would go here...

            break  # Exit loop if successful

        except Exception as e:
            logger.error(f"💥 Critical error: {str(e)}")
            if driver:
                driver.quit()
            retry_count += 1
            logger.info("🔄 Restarting in 60 seconds...")
            time.sleep(60)

if __name__ == "__main__":
    main()
