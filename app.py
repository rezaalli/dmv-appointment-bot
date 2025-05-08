# app.py
import time
import os
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DMV_URL = "https://www.dmv.ca.gov/portal/appointments/select-location/A"
ZIP_CODE = "92108"
LOCATION_SELECTOR = "//button[contains(text(), 'Select Location')]"
NO_DATES_AVAILABLE_TEXT = "Sorry, no dates available"

def init_driver():
    logger.info("🌀 Initializing Chrome Driver")
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30)
    return driver

def visit_dmv_page(driver):
    logger.info("🌐 Navigating to DMV Page")
    driver.get(DMV_URL)
    current_url = driver.current_url
    
    if "select-appointment-type" in current_url:
        logger.warning(f"⚠️ Redirected to {current_url}, forcing navigation back.")
        driver.get(DMV_URL)
        
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Enter City or ZIP Code']")))
    zip_input = driver.find_element(By.XPATH, "//input[@placeholder='Enter City or ZIP Code']")
    zip_input.clear()
    zip_input.send_keys(ZIP_CODE)
    zip_input.submit()
    time.sleep(3)  # Allow page to reload
    logger.info("✅ Zip code entered and search submitted.")

def select_location(driver):
    logger.info("📍 Selecting location...")
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
    while True:
        try:
            logger.info("🚀 Starting Appointment Bot")
            driver = init_driver()
            visit_dmv_page(driver)
            
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
