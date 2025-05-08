from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from anticaptchaofficial.imagecaptcha import imagecaptcha
from webdriver_manager.chrome import ChromeDriverManager
import time
import threading
import logging
import os
import shutil

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Flask app setup
app = Flask(__name__)

# Configuration
first_name = "Ashley"
last_name = "Barley"
phone_number = "808-927-6227"
email_address = "barleyohana@gmail.com"
preferred_locations = ["San Diego Clairemont", "San Diego", "Chula Vista"]
captcha_api_key = os.getenv("CAPTCHA_API_KEY")
date_range = list(range(3, 19))  # June 3 to June 18
primary_zip_code = "92108"

# Anti-Captcha Solver
solver = imagecaptcha()
solver.set_verbose(1)
solver.set_key(captcha_api_key)

# Global variables for status
status = {
    "current_location": "",
    "last_checked": "",
    "appointment_found": False,
    "last_error": ""
}

# Initialize the ChromeDriver
def initialize_driver():
    logging.info("🖥️ Initializing Chrome Driver")
    
    # Path for the Chrome binary
    chrome_path = shutil.which("google-chrome")
    if not chrome_path:
        logging.error("Google Chrome not found on PATH. Exiting.")
        exit(1)

    # Chrome options
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = chrome_path
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--window-size=1280x1024")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument("--disable-application-cache")
    chrome_options.add_argument("--disable-crash-reporter")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--disable-in-process-stack-traces")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--output=/dev/null")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-client-side-phishing-detection")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-infobars")

    # Start the ChromeDriver
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)  # Prevent long waits
    driver.maximize_window()
    return driver

def solve_captcha(driver):
    try:
        captcha_image = driver.find_element(By.CSS_SELECTOR, "img.captcha-image-selector")
        captcha_image.screenshot("captcha.png")

        result = solver.solve_and_return_solution("captcha.png")
        if result != 0:
            logging.info(f"✅ CAPTCHA Solved: {result}")
            captcha_input = driver.find_element(By.ID, 'captcha-input-id')
            captcha_input.send_keys(result)
            return True
        else:
            logging.error("❌ CAPTCHA solve failed.")
            return False
    except Exception as e:
        logging.error(f"❌ Error solving CAPTCHA: {e}")
        status["last_error"] = str(e)
        return False

def select_location(driver, location_name):
    try:
        buttons = driver.find_elements(By.XPATH, "//button[contains(text(),'Select Location')]")
        for button in buttons:
            parent = button.find_element(By.XPATH, "./..")
            if location_name in parent.text:
                button.click()
                logging.info(f"✅ Location selected: {location_name}")
                status["current_location"] = location_name
                return True
        return False
    except Exception as e:
        logging.error(f"❌ Error selecting location: {e}")
        status["last_error"] = str(e)
        return False

def find_available_dates(driver):
    try:
        available_days = driver.find_elements(By.XPATH, "//div[contains(@class, 'Open Times')]")
        for day in available_days:
            date_text = day.text.strip()
            if date_text.isdigit() and int(date_text) in date_range:
                logging.info(f"📅 Available date found: {date_text}")
                day.click()
                return True
        return False
    except Exception as e:
        logging.error(f"❌ Error finding available dates: {e}")
        status["last_error"] = str(e)
        return False

def fill_form(driver):
    try:
        driver.find_element(By.ID, 'first_name').send_keys(first_name)
        driver.find_element(By.ID, 'last_name').send_keys(last_name)
        driver.find_element(By.ID, 'phone_number').send_keys(phone_number)
        driver.find_element(By.ID, 'email').send_keys(email_address)
        driver.find_element(By.XPATH, "//label[contains(text(),'Text me')]").click()
        driver.find_element(By.XPATH, "//button[contains(text(),'Submit')]").click()
        logging.info("✅ Appointment successfully booked!")
        status["appointment_found"] = True
        return True
    except Exception as e:
        logging.error(f"❌ Error filling the form: {e}")
        status["last_error"] = str(e)
        return False

def search_appointments():
    driver = initialize_driver()
    while not status["appointment_found"]:
        for location in preferred_locations:
            try:
                driver.get("https://www.dmv.ca.gov/portal/appointments/select-location/S")
                if not select_location(driver, location):
                    continue

                time.sleep(2)
                if find_available_dates(driver):
                    if fill_form(driver):
                        driver.quit()
                        return
            except Exception as e:
                logging.error(f"❌ Error during appointment search: {e}")
                status["last_error"] = str(e)
            time.sleep(120)

# Flask Endpoints
@app.route('/')
def home():
    return "🎉 DMV Bot is running and searching for appointments!"

@app.route('/status')
def get_status():
    return jsonify(status)

def run_bot():
    threading.Thread(target=search_appointments).start()

if __name__ == "__main__":
    run_bot()
    app.run(host="0.0.0.0", port=5000)
