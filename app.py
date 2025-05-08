# app.py
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Selenium Driver Setup ---
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

# --- Main Navigation Logic ---
def navigate_to_dmv_page(driver):
    """Navigate to the DMV location selection page."""
    try:
        logger.info("🌎 Navigating to DMV Page")
        driver.get("https://www.dmv.ca.gov/portal/appointments/select-location/A")
        
        # Wait for page to load
        time.sleep(5)

        # Verify we reached the selection page
        if driver.find_element(By.XPATH, "//h1[contains(text(), 'Which office would you like to visit?')]"):
            logger.info("✅ Successfully reached DMV Location Selection page.")
            return True
    except (TimeoutException, NoSuchElementException) as e:
        logger.error(f"❌ Error navigating to DMV page: {str(e)}")
    return False

# --- Main Execution ---
driver = init_driver()
if navigate_to_dmv_page(driver):
    logger.info("🎉 Phase 1 Completed Successfully.")
else:
    logger.error("💥 Phase 1 Failed. Unable to reach DMV page.")
driver.quit()
