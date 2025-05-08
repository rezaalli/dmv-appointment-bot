import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from flask import Flask, render_template
from threading import Thread

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# User Information
USER_INFO = {
    "first_name": "Ashley",
    "last_name": "Barley",
    "email": "barleyohana@gmail.com",
    "phone": "808-927-6227"
}

# Target Information
APPOINTMENT_URL = "https://www.dmv.ca.gov/portal/appointments/select-appointment-type/ukpx.aspx?pid=1&ruleid=341"
ZIP_CODE = "92108"
PREFERRED_LOCATION = "San Diego Clairemont"
DATE_RANGE = ("June 3", "June 18")

# Initialize Chrome WebDriver
def create_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# Navigate to the appointment page
def navigate_to_appointment_page(driver):
    logging.info(f"🌐 Navigating to appointment page")
    driver.get(APPOINTMENT_URL)
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Office Visit')]"))
        )
        logging.info("✅ Successfully loaded appointment page.")
    except Exception as e:
        logging.error(f"❌ Error loading appointment page: {str(e)}")
        driver.quit()
        return False
    return True

# Search for location and select
def search_and_select_location(driver):
    logging.info("🔎 Searching for location")
    zip_input = driver.find_element(By.XPATH, "//input[@placeholder='Enter City or ZIP Code']")
    zip_input.clear()
    zip_input.send_keys(ZIP_CODE)
    zip_input.submit()
    time.sleep(2)

    try:
        location_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//button[contains(text(), '{PREFERRED_LOCATION}')]"))
        )
        location_button.click()
        logging.info(f"✅ Selected location: {PREFERRED_LOCATION}")
        return True
    except Exception as e:
        logging.error(f"❌ Failed to select location: {str(e)}")
        return False

# Select the date and time
def select_date_and_time(driver):
    logging.info("📅 Selecting a date and time")
    try:
        date_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, f"//div[@aria-label='Open Times'][contains(text(), '{DATE_RANGE[0]}')]"))
        )
        date_button.click()
        logging.info(f"✅ Date selected: {DATE_RANGE[0]}")
        
        # Select the first available time
        time_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "(//button[contains(@class, 'select-time-button')])[1]"))
        )
        time_button.click()
        logging.info(f"✅ Time slot selected.")
        return True
    except Exception as e:
        logging.error(f"❌ Failed to select date or time: {str(e)}")
        return False

# Fill out user information
def fill_out_information(driver):
    logging.info("📝 Filling out user information")
    try:
        driver.find_element(By.ID, "FirstName").send_keys(USER_INFO['first_name'])
        driver.find_element(By.ID, "LastName").send_keys(USER_INFO['last_name'])
        driver.find_element(By.ID, "Email").send_keys(USER_INFO['email'])
        driver.find_element(By.ID, "Phone").send_keys(USER_INFO['phone'])

        # Select the "Text me" option
        text_option = driver.find_element(By.XPATH, "//label[contains(text(), 'Text me')]")
        text_option.click()
        
        submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
        submit_button.click()
        
        logging.info("✅ Information submitted successfully.")
        return True
    except Exception as e:
        logging.error(f"❌ Failed to submit information: {str(e)}")
        return False

# Main bot process
def appointment_bot():
    while True:
        logging.info("🚀 Starting Appointment Bot")
        driver = create_driver()

        if navigate_to_appointment_page(driver):
            if search_and_select_location(driver):
                if select_date_and_time(driver):
                    if fill_out_information(driver):
                        logging.info("🎉 Appointment successfully booked!")
                        driver.quit()
                        break
        logging.info("🔄 Retrying in 60 seconds...")
        driver.quit()
        time.sleep(60)

# Flask route for monitoring
@app.route('/')
def home():
    return render_template('index.html', status="Bot is running...")

# Start the bot in a separate thread
def start_bot():
    bot_thread = Thread(target=appointment_bot)
    bot_thread.start()

# Start Flask app
if __name__ == '__main__':
    start_bot()
    app.run(host='0.0.0.0', port=5000)
