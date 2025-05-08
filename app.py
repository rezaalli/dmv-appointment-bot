# app.py
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DMV Configuration ---
DMV_URL = "https://www.dmv.ca.gov/portal/appointments/select-location/A"
ZIP_CODE = "92108"
LOCATION_NAME = "San Diego Clairemont"

# --- Initialize Selenium Driver ---
def init_driver():
    """Initialize the Selenium WebDriver."""
    logger.info("🚀 Initializing Chrome Driver")
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(30)
    return driver

# --- Navigate to DMV Page ---
def navigate_to_dmv_page(driver):
    """Navigate to the DMV location selection page."""
    try:
        logger.info("🌎 Navigating to DMV Page")
        driver.get(DMV_URL)
        
        # Wait for page to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Which office would you like to visit?')]"))
        )
        logger.info("✅ Successfully reached DMV Location Selection page.")
        return True
    except (TimeoutException, NoSuchElementException) as e:
        logger.error(f"❌ Error navigating to DMV page: {str(e)}")
    return False

# --- Select Location ---
def select_location(driver):
    """Select the preferred DMV location."""
    try:
        logger.info(f"🗺️ Searching for {LOCATION_NAME}")
        
        # Search for the location button and click it
        location_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, f"//button[contains(text(), '{LOCATION_NAME}')]"))
        )
        location_button.click()
        logger.info(f"✅ Successfully clicked {LOCATION_NAME}")
        return True
    except (TimeoutException, NoSuchElementException) as e:
        logger.error(f"❌ Location not found or not clickable: {str(e)}")
        return False

# --- Main Bot Logic ---
def main_loop():
    """Main bot logic for appointment booking."""
    while True:
        driver = init_driver()
        
        if navigate_to_dmv_page(driver):
            if select_location(driver):
                logger.info("🎉 Successfully navigated and clicked location!")
                break
            else:
                logger.warning("🔄 Location selection failed. Retrying in 60 seconds...")
        
        # If failed, restart cycle
        logger.info("🔄 Restarting cycle in 60 seconds...")
        driver.quit()
        time.sleep(60)

    driver.quit()
    logger.info("✅ Task Completed Successfully.")

# --- Start the Bot ---
if __name__ == "__main__":
    main_loop()
