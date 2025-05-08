import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from flask import Flask, jsonify
from selenium.common.exceptions import NoSuchElementException, WebDriverException

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app for health checks
app = Flask(__name__)

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200

# Configuration
APPOINTMENT_URL = "https://www.dmv.ca.gov/portal/appointments/select-appointment-type/ukpx.aspx?pid=1&ruleid=341"
RETRY_INTERVAL = 60  # 60 seconds
WATCHDOG_INTERVAL = 300  # 5 minutes
ZIP_CODE = "92108"
LOCATION_NAME = "San Diego Clairemont"
PREFERRED_DATES = ["June 3", "June 4", "June 5", "June 6", "June 7", "June 8", "June 9", "June 10", "June 11"]

# Options for headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")


def initialize_driver():
    """Initializes the Chrome WebDriver with options."""
    logger.info("🌐 Starting Chrome Driver")
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(APPOINTMENT_URL)
        return driver
    except WebDriverException as e:
        logger.error(f"❌ WebDriver Initialization Failed: {e}")
        return None


def search_and_book_appointment():
    """Main logic for navigating the DMV site and booking an appointment."""
    driver = initialize_driver()
    if not driver:
        return

    try:
        # Selecting First-time DL Application
        logger.info("🖱️ Clicking First-time DL Application")
        driver.find_element(By.LINK_TEXT, "First-time DL Application").click()
        time.sleep(2)

        # Selecting "Get an Appointment"
        logger.info("🖱️ Selecting 'Get an Appointment'")
        driver.get(APPOINTMENT_URL)
        time.sleep(2)

        # Enter ZIP Code and search
        logger.info("📍 Entering ZIP Code and searching")
        zip_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Enter City or ZIP Code']")
        zip_input.send_keys(ZIP_CODE)
        driver.find_element(By.CSS_SELECTOR, "button[aria-label='Search']").click()
        time.sleep(3)

        # Select the preferred location
        logger.info("📌 Selecting the preferred location")
        location_button = driver.find_element(By.XPATH, f"//button[contains(text(), '{LOCATION_NAME}')]")
        location_button.click()
        time.sleep(2)

        # Choose preferred date
        logger.info("📅 Selecting preferred date")
        for date in PREFERRED_DATES:
            try:
                date_button = driver.find_element(By.XPATH, f"//button[contains(text(), '{date}')]")
                date_button.click()
                logger.info(f"✅ Date {date} selected")
                break
            except NoSuchElementException:
                logger.info(f"❌ Date {date} not available")
        
        # Complete the form with personal information
        logger.info("📝 Filling out the personal information")
        driver.find_element(By.ID, "FirstName").send_keys("Ashley")
        driver.find_element(By.ID, "LastName").send_keys("Barley")
        driver.find_element(By.ID, "Email").send_keys("barleyohana@gmail.com")
        driver.find_element(By.ID, "Phone").send_keys("808-927-6227")
        driver.find_element(By.CSS_SELECTOR, "input[value='text']").click()
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        logger.info("🎉 Appointment successfully booked!")

    except NoSuchElementException as e:
        logger.error(f"❌ Error Occurred: {e}")
    except WebDriverException as e:
        logger.error(f"❌ WebDriverException: {e}")
    finally:
        driver.quit()


def watchdog():
    """Watches for crashes and restarts the bot if necessary."""
    while True:
        logger.info("👀 Watchdog: Checking bot health")
        try:
            search_and_book_appointment()
        except Exception as e:
            logger.error(f"🔥 Bot crashed with error: {e}. Restarting in {RETRY_INTERVAL} seconds...")
            time.sleep(RETRY_INTERVAL)
        logger.info(f"⏳ Retrying in {WATCHDOG_INTERVAL} seconds...")
        time.sleep(WATCHDOG_INTERVAL)


# Start Flask in a separate thread
from threading import Thread
Thread(target=lambda: app.run(host='0.0.0.0', port=5000)).start()

# Start Watchdog
watchdog()
