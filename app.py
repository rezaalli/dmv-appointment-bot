# app.py
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Proxy list
proxies = [
    "35.86.81.136:3128",
    "18.132.36.51:3128",
    "80.1.215.23:8888",
    "13.126.217.46:3128",
    "119.156.195.173:3128",
    # Add more proxies as needed...
]

# Initialize driver
def init_driver():
    logger.info("🚀 Initializing Chrome Driver")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    # Set up ChromeDriver explicitly
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(30)
    logger.info("✅ Chrome Driver Initialized Successfully")
    return driver

# Proxy rotation
def get_random_proxy():
    return random.choice(proxies)

# Check if the proxy is alive
def is_proxy_alive(proxy):
    try:
        response = requests.get("https://www.dmv.ca.gov", proxies={"http": proxy, "https": proxy}, timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"⚠️ Proxy {proxy} is not reachable: {e}")
        return False

# Start navigation
def navigate_to_dmv(driver):
    driver.get("https://www.dmv.ca.gov/portal/appointments/select-location/A")
    logger.info("🌐 Navigated to DMV Location Selection Page")
    time.sleep(3)

# Main loop
def main_loop():
    while True:
        try:
            driver = init_driver()
            navigate_to_dmv(driver)
            
            # Check if page is loaded correctly
            if "Which office would you like to visit?" not in driver.page_source:
                raise Exception("❌ Page did not load properly.")
            
            logger.info("✅ Page Loaded Successfully - Ready for next step.")
            
            # Example: Select a location (customize this step as needed)
            select_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Select Location')]")
            if select_buttons:
                select_buttons[0].click()
                logger.info("🏢 Location selected.")
            else:
                logger.warning("⚠️ No locations found, restarting in 60 seconds...")
                driver.quit()
                time.sleep(60)
                continue
            
            # Further steps (Form filling, etc.) can go here...
            
            driver.quit()
            time.sleep(30)  # Wait before retrying
        
        except Exception as e:
            logger.error(f"❌ Critical error: {e}")
            if driver:
                driver.quit()
            time.sleep(60)  # Retry after a minute

# Run the bot
if __name__ == "__main__":
    main_loop()
