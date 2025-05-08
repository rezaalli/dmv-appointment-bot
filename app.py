import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from flask import Flask, jsonify

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app for health checks
app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200

# Configuration
START_URL = "https://www.dmv.ca.gov/portal/appointments/select-location/A"
ZIP_CODE = "92108"
LOCATION_NAME = "San Diego Clairemont"
PREFERRED_DATES = ["June 3", "June 4", "June 5", "June 6", "June 7", "June 8", "June 9", "June 10", "June 11"]
RETRY_INTERVAL = 60  # 60 seconds

# Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

def initialize_driver():
    try:
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
        driver.get(START_URL)
        logger.info("🌐 Navigated to Select Location page.")
        return driver
    except Exception as e:
        logger.error(f"🚨 Error initializing driver: {e}")
        return None

def enter_zip_and_search(driver):
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Enter City or ZIP Code']")))
        zip_input = driver.find_element(By.XPATH, "//input[@placeholder='Enter City or ZIP Code']")
        zip_input.send_keys(ZIP_CODE)
        zip_input.submit()
        logger.info(f"✅ Entered Zip Code: {ZIP_CODE}")
    except NoSuchElementException:
        logger.error("❌ Zip code input not found!")
        return False
    return True

def select_location(driver):
    try:
        WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, f"//button[contains(text(), '{LOCATION_NAME}')]")))
        location_button = driver.find_element(By.XPATH, f"//button[contains(text(), '{LOCATION_NAME}')]")
        location_button.click()
        logger.info(f"✅ Selected location: {LOCATION_NAME}")
    except NoSuchElementException:
        logger.error("❌ Location button not found!")
        return False
    return True

def choose_date_and_time(driver):
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "calendar-day")))
        days = driver.find_elements(By.CLASS_NAME, "calendar-day")
        for day in days:
            if day.text in PREFERRED_DATES:
                day.click()
                logger.info(f"✅ Selected date: {day.text}")
                return True
        logger.info("🔍 No preferred dates available, retrying in 60 seconds.")
    except NoSuchElementException:
        logger.error("❌ Calendar not found!")
    return False

def fill_appointment_form(driver):
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.NAME, "firstName")))
        driver.find_element(By.NAME, "firstName").send_keys("Ashley")
        driver.find_element(By.NAME, "lastName").send_keys("Barley")
        driver.find_element(By.NAME, "email").send_keys("barleyohana@gmail.com")
        driver.find_element(By.NAME, "phone").send_keys("808-927-6227")
        driver.find_element(By.XPATH, "//label[contains(text(), 'Text me')]").click()
        driver.find_element(By.XPATH, "//button[text()='Submit']").click()
        logger.info("📌 Appointment successfully booked!")
    except NoSuchElementException as e:
        logger.error(f"❌ Form element not found: {e}")

def main():
    while True:
        driver = initialize_driver()
        if not driver:
            time.sleep(RETRY_INTERVAL)
            continue

        if enter_zip_and_search(driver):
            if select_location(driver):
                if choose_date_and_time(driver):
                    fill_appointment_form(driver)
        
        logger.info(f"🔄 Retrying in {RETRY_INTERVAL} seconds...")
        driver.quit()
        time.sleep(RETRY_INTERVAL)

if __name__ == "__main__":
    main()
