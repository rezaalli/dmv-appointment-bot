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

def get_random_proxy():
    return random.choice(PROXY_LIST)

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

def navigate_full_flow(driver):
    logger.info("🌐 Navigating through full DMV flow")
    driver.get(DMV_START_URL)
    
    # Step 1: Click "First-time DL Application"
    try:
        logger.info("📝 Clicking 'First-time DL Application'")
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "First-time DL Application"))).click()
    except Exception as e:
        logger.error("❌ Could not click 'First-time DL Application'")
        return False
    
    # Step 2: Click "Get an Appointment"
    try:
        logger.info("📅 Clicking 'Get an Appointment'")
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Get an Appointment')]"))).click()
    except Exception as e:
        logger.error("❌ Could not click 'Get an Appointment'")
        return False

    # Step 3: Navigate to location selection
    logger.info("🌐 Navigating to location selection")
    driver.get("https://www.dmv.ca.gov/portal/appointments/select-location/A")
    
    # Check if it redirected back
    if "select-appointment-type" in driver.current_url:
        logger.warning("⚠️ Redirected back, retrying full navigation")
        return False
    
    return True

def visit_and_search_location(driver):
    logger.info("📍 Selecting location with ZIP code")
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Enter City or ZIP Code']")))
    zip_input = driver.find_element(By.XPATH, "//input[@placeholder='Enter City or ZIP Code']")
    zip_input.clear()
    zip_input.send_keys(ZIP_CODE)
    zip_input.submit()
    time.sleep(3)  # Allow page to reload
    logger.info("✅ Zip code entered and search submitted.")

def select_location(driver):
    logger.info("📌 Checking location availability")
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, LOCATION_SELECTOR))
        )
        
        buttons = driver.find_elements(By.XPATH, LOCATION_SELECTOR)
        
        for button in buttons:
            button_text = button.text
            if NO_DATES_AVAILABLE_TEXT not in button_text:
                button.click()
                logger.info("✅ Location selected.")
                return True
        
        logger.warning("⚠️ All locations say 'No dates available'. Restarting...")
        driver.quit()
        return False
        
    except (NoSuchElementException, TimeoutException) as e:
        logger.error("❌ Element not found or timeout: %s", str(e))
        page_source = driver.page_source
        with open("/mnt/data/error_page.html", "w") as f:
            f.write(page_source)
        driver.save_screenshot('/mnt/data/error_screenshot.png')
        driver.quit()
        return False

def main():
    retry_count = 0
    while True:
        try:
            if retry_count >= MAX_RETRIES:
                logger.error("💥 Maximum retries reached. Restarting with a new Proxy...")
                retry_count = 0
            logger.info("🚀 Starting Appointment Bot")
            driver = init_driver()
            if not navigate_full_flow(driver):
                retry_count += 1
                driver.quit()
                continue
            
            visit_and_search_location(driver)
            
            if select_location(driver):
                logger.info("🎉 Appointment Found and Booked!")
                break
            
            logger.info("🔄 Restarting in 60 seconds...")
            time.sleep(60)

        except Exception as e:
            logger.error("💥 Critical error: %s", str(e))
            if driver:
                driver.quit()
            logger.info("🔄 Restarting in 60 seconds...")
            time.sleep(60)

if __name__ == "__main__":
    main()
