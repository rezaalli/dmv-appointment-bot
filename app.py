# app.py
import os
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import requests
from requests.exceptions import ProxyError, ConnectTimeout

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Proxy List ---
PROXY_LIST = [
    "35.86.81.136:3128",
    "18.132.36.51:3128",
    "80.1.215.23:8888",
    "13.126.217.46:3128",
    "119.156.195.173:3128",
    "34.221.119.219:999",
    "54.184.124.175:14581",
    "52.56.248.120:10001",
    "18.236.175.208:10001",
    "18.175.118.106:999"
]

FAILED_PROXIES = {}

# --- Proxy Validation ---
def is_proxy_alive(proxy):
    """Check if a proxy is alive by pinging a simple site."""
    try:
        response = requests.get("https://www.dmv.ca.gov", proxies={"http": proxy, "https": proxy}, timeout=5)
        if response.status_code == 200:
            logger.info(f"✅ Proxy {proxy} is alive.")
            return True
        else:
            logger.warning(f"⚠️ Proxy {proxy} failed with status: {response.status_code}")
            return False
    except (ProxyError, ConnectTimeout) as e:
        logger.warning(f"⚠️ Proxy {proxy} is not reachable. Error: {e}")
        return False

def get_random_proxy():
    """Rotate through the proxy list and return a working proxy."""
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

# --- Selenium Initialization ---
def init_driver(proxy=None):
    """Initialize Chrome driver with or without proxy."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    if proxy:
        logger.info(f"🌐 Using Proxy: {proxy}")
        chrome_options.add_argument(f'--proxy-server={proxy}')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(30)
    return driver

# --- Main Navigation Logic ---
def navigate_dmv(driver):
    """Navigate the DMV Appointment System."""
    try:
        driver.get("https://www.dmv.ca.gov/portal/appointments/select-location/A")
        logger.info("🌎 Navigating to DMV Page")

        # Example of trying to find an element
        try:
            driver.find_element(By.XPATH, "//button[contains(text(), 'Select Location')]")
            logger.info("✅ Location buttons found.")
        except NoSuchElementException:
            logger.error("❌ Element not found or timeout. Retrying in 60 seconds...")
            time.sleep(60)
            return False
        
        # Check for "no dates available" message
        no_dates = driver.find_elements(By.XPATH, "//span[contains(text(), 'no dates available')]")
        if no_dates:
            logger.warning("⚠️ No dates available. Restarting...")
            return False
        
        # Additional navigation logic here
        
        return True
    except (TimeoutException, Exception) as e:
        logger.error(f"💥 Critical error: {str(e)}")
        return False

# --- Main Loop ---
while True:
    logger.info("🚀 Starting Appointment Bot")
    proxy = get_random_proxy()
    driver = init_driver(proxy)

    if not navigate_dmv(driver):
        logger.info("🔄 Restarting cycle...")
        driver.quit()
        time.sleep(60)
        continue
    
    logger.info("✅ Task completed successfully.")
    driver.quit()
    break
