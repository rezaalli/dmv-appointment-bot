import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
START_URL = "https://www.dmv.ca.gov/portal/appointments/select-location/A"
RETRY_LIMIT = 5
RETRY_WAIT = 30

# Learning memory to store successful navigation
navigation_memory = {}

def initialize_driver():
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Correct driver initialization
        driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=chrome_options)
        driver.get(START_URL)
        logger.info("🌐 Navigated to Select Location page.")
        return driver
    except Exception as e:
        logger.error(f"🚨 Error initializing driver: {e}")
        return None

def retry_on_failure(func):
    """
    Decorator to retry functions on failure.
    """
    def wrapper(*args, **kwargs):
        attempts = 0
        while attempts < RETRY_LIMIT:
            try:
                result = func(*args, **kwargs)
                if result:
                    return result
                else:
                    attempts += 1
                    logger.warning(f"⚠️ Attempt {attempts}/{RETRY_LIMIT} failed, retrying in {RETRY_WAIT} seconds...")
                    time.sleep(RETRY_WAIT)
            except Exception as e:
                attempts += 1
                logger.error(f"🚨 Error: {e}. Retrying in {RETRY_WAIT} seconds...")
                time.sleep(RETRY_WAIT)
        logger.error(f"❌ Failed after {RETRY_LIMIT} attempts.")
        return None
    return wrapper

@retry_on_failure
def select_location(driver):
    try:
        logger.info("📌 Selecting Location...")
        if "Select Location" not in navigation_memory:
            # Find the zip input and search
            zip_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Enter City or ZIP Code']")))
            zip_input.send_keys("92108")
            zip_input.submit()
            navigation_memory["Select Location"] = True
        return True
    except Exception as e:
        navigation_memory.pop("Select Location", None)
        logger.error(f"🚨 Error during location selection: {e}")
        return False

@retry_on_failure
def select_preferred_office(driver):
    try:
        logger.info("🏢 Selecting San Diego Clairemont Office...")
        if "Select Office" not in navigation_memory:
            office_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Select Location')]")))
            office_button.click()
            navigation_memory["Select Office"] = True
        return True
    except Exception as e:
        navigation_memory.pop("Select Office", None)
        logger.error(f"🚨 Error selecting preferred office: {e}")
        return False

@retry_on_failure
def select_available_date(driver):
    try:
        logger.info("📅 Selecting Available Date...")
        if "Select Date" not in navigation_memory:
            open_dates = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='day open']")))
            for date in open_dates:
                if "Open Times" in date.text:
                    date.click()
                    navigation_memory["Select Date"] = True
                    return True
        return False
    except Exception as e:
        navigation_memory.pop("Select Date", None)
        logger.error(f"🚨 Error selecting available date: {e}")
        return False

@retry_on_failure
def fill_out_information(driver):
    try:
        logger.info("✍️ Filling out information...")
        if "Fill Information" not in navigation_memory:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "FirstName"))).send_keys("Ashley")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "LastName"))).send_keys("Barley")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "EmailAddress"))).send_keys("barleyohana@gmail.com")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "PhoneNumber"))).send_keys("808-927-6227")
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//input[@type='checkbox']"))).click()
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Submit')]"))).click()
            navigation_memory["Fill Information"] = True
        return True
    except Exception as e:
        navigation_memory.pop("Fill Information", None)
        logger.error(f"🚨 Error filling out information: {e}")
        return False

def start_appointment_bot():
    driver = initialize_driver()
    if not driver:
        logger.error("❌ Failed to initialize driver.")
        return
    
    steps = [
        select_location,
        select_preferred_office,
        select_available_date,
        fill_out_information
    ]

    for step in steps:
        if not step(driver):
            logger.error("❌ Failed at step: {}".format(step.__name__))
            driver.quit()
            start_appointment_bot()
            return
    
    logger.info("✅ Appointment successfully scheduled!")
    driver.quit()

start_appointment_bot()
