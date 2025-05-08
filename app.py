from flask import Flask, render_template
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
import threading

app = Flask(__name__)

# Global configuration
START_URL = "https://www.dmv.ca.gov/portal/appointments/select-location/A"
PREFERRED_LOCATION = "San Diego Clairemont"
RETRY_INTERVAL = 60  # Retry every 60 seconds if failure
MAX_RETRIES = 5      # Maximum retries before full restart

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global driver instance
driver = None

def initialize_driver():
    """
    Initializes the Chrome WebDriver with headless options and navigation to the start URL.
    Handles WebDriver exceptions and retries intelligently.
    """
    global driver
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
        driver.get(START_URL)
        logger.info("🌐 Navigated to Select Location page.")
        return driver
    except Exception as e:
        logger.error(f"🚨 Error initializing driver: {e}")
        return None


def retry_on_failure(func):
    """
    Decorator to retry functions if they fail.
    """
    def wrapper(*args, **kwargs):
        for attempt in range(MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"⚠️ Attempt {attempt + 1} failed with error: {e}")
                time.sleep(RETRY_INTERVAL)
        logger.critical(f"❌ Maximum retries reached for {func.__name__}")
        return False
    return wrapper


@retry_on_failure
def select_location():
    """
    Selects the preferred location from the list.
    """
    logger.info("📍 Selecting preferred location...")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "office-zip")))
    search_box = driver.find_element(By.ID, "office-zip")
    search_box.clear()
    search_box.send_keys("92108")
    search_box.submit()
    
    WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, f"//button[contains(text(), '{PREFERRED_LOCATION}')]"))
    ).click()
    logger.info(f"✅ Successfully selected location: {PREFERRED_LOCATION}")


@retry_on_failure
def select_date():
    """
    Selects the preferred date if available.
    """
    logger.info("📅 Searching for available dates...")
    available_dates = driver.find_elements(By.CLASS_NAME, "open-date")
    
    for date in available_dates:
        if "June" in date.text or "July" in date.text:
            logger.info(f"🗓️ Selecting available date: {date.text}")
            date.click()
            return True
    raise Exception("No suitable dates found.")


@retry_on_failure
def fill_form_and_submit():
    """
    Fills the form and submits the appointment request.
    """
    logger.info("✍️ Filling the appointment form...")
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.NAME, "firstName"))
    ).send_keys("Ashley")

    driver.find_element(By.NAME, "lastName").send_keys("Barley")
    driver.find_element(By.NAME, "email").send_keys("barleyohana@gmail.com")
    driver.find_element(By.NAME, "phone").send_keys("808-927-6227")

    logger.info("📤 Submitting the form...")
    driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]").click()
    logger.info("🎉 Appointment successfully booked!")


def appointment_bot():
    """
    Main bot loop with recovery and resilience mechanisms.
    """
    global driver
    while True:
        try:
            if driver is None:
                driver = initialize_driver()
            
            if not driver:
                logger.error("❌ Driver initialization failed, retrying...")
                time.sleep(RETRY_INTERVAL)
                continue

            select_location()
            select_date()
            fill_form_and_submit()
            logger.info("🎉 All steps completed successfully.")
            break

        except Exception as e:
            logger.error(f"🔄 Encountered error: {e}, restarting process in 60 seconds...")
            if driver:
                driver.quit()
            driver = initialize_driver()
            time.sleep(RETRY_INTERVAL)


@app.route('/')
def home():
    return render_template('index.html', status="Bot is running...")


def start_bot():
    """
    Starts the bot in a separate thread to keep the Flask app responsive.
    """
    bot_thread = threading.Thread(target=appointment_bot)
    bot_thread.start()


# Start the bot when the app launches
start_bot()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
