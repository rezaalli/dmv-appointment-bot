from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import logging
import os

# Configuration
APPOINTMENT_URL = "https://www.dmv.ca.gov/portal/appointments/select-appointment-type/ukpx.aspx?pid=1&ruleid=341"
PREFERRED_LOCATION = "San Diego Clairemont"
PREFERRED_ZIP = "92108"
DATE_RANGE = ("2025-06-03", "2025-06-18")
RETRY_LIMIT = 3
RETRY_INTERVAL = 60  # Seconds

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def create_driver():
    """Create and configure the WebDriver instance."""
    logging.info("🌀 Starting Chrome Driver")
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless=new")
    chrome_options.page_load_strategy = 'normal'
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(60)
    return driver


def start_bot():
    """Main logic to start the bot and handle navigation and retries."""
    driver = create_driver()
    retries = 0

    while retries < RETRY_LIMIT:
        try:
            logging.info("🚀 Starting Appointment Bot")
            driver.get(APPOINTMENT_URL)

            # Step 1: Select First-time DL Application
            logging.info("📝 Clicking First-time DL Application")
            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "First-time DL Application"))
            ).click()

            # Step 2: Click 'Get an Appointment'
            logging.info("🖱️ Selecting 'Get an Appointment'")
            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Get an Appointment')]"))
            ).click()

            # Step 3: Select REAL ID
            logging.info("📝 Selecting 'REAL ID Driver's License / REAL ID'")
            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "REAL ID Driver's License / REAL ID"))
            ).click()

            # Step 4: Enter Zip Code
            logging.info(f"📌 Entering Zip Code: {PREFERRED_ZIP}")
            zip_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Enter City or ZIP Code']"))
            )
            zip_input.send_keys(PREFERRED_ZIP)
            zip_input.submit()

            # Step 5: Select Preferred Location
            logging.info(f"📍 Selecting Preferred Location: {PREFERRED_LOCATION}")
            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, f"//button[contains(text(), '{PREFERRED_LOCATION}')]"))
            ).click()

            # Step 6: Check for available dates
            logging.info(f"📅 Searching for available dates between {DATE_RANGE[0]} and {DATE_RANGE[1]}")
            available_dates = driver.find_elements(By.CLASS_NAME, "open-times")

            if not available_dates:
                logging.warning("⚠️ No dates available. Retrying in 60 seconds...")
                time.sleep(RETRY_INTERVAL)
                retries += 1
                continue

            # If dates found, proceed to select
            available_dates[0].click()

            # Step 7: Fill out the form
            logging.info("🖊️ Filling out appointment information")
            driver.find_element(By.ID, "firstName").send_keys("Ashley")
            driver.find_element(By.ID, "lastName").send_keys("Barley")
            driver.find_element(By.ID, "email").send_keys("barleyohana@gmail.com")
            driver.find_element(By.ID, "phone").send_keys("808-927-6227")

            # Step 8: Submit the form
            logging.info("✅ Submitting the appointment form")
            driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]").click()

            # If we reached this point, the process was successful
            logging.info("🎉 Appointment successfully booked!")
            break

        except Exception as e:
            logging.error(f"❌ Error Occurred: {e}")
            retries += 1
            logging.info(f"🔄 Retrying in {RETRY_INTERVAL} seconds... (Attempt {retries}/{RETRY_LIMIT})")
            time.sleep(RETRY_INTERVAL)
            if retries == RETRY_LIMIT:
                logging.error("💥 Maximum retries reached. Restarting session...")
                driver.quit()
                driver = create_driver()
                retries = 0


if __name__ == "__main__":
    while True:
        try:
            start_bot()
        except Exception as main_error:
            logging.error(f"🔥 Main loop crashed: {main_error}")
            logging.info("♻️ Restarting bot after 60 seconds...")
            time.sleep(60)
