from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from anticaptchaofficial.imagecaptcha import imagecaptcha
import undetected_chromedriver as uc
import time
import threading
import logging
import base64
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
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    # Start the ChromeDriver
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    return driver

def solve_captcha(driver):
    try:
        captcha_image = driver.find_element(By.CSS_SELECTOR, "img.captcha-image-selector")
        captcha_image.screenshot("captcha.png")

        result = solver.solve_and_return_solution("captcha.png")
        if result != 0:
            logging.info(f"✅ CAPTCHA Solved: {result}")
            captcha_input = driver.find_element(By.ID, 'captcha-input-id')  # Adjust the ID as needed
            captcha_input.send_keys(result)
            return True
        else:
            logging.error("❌ CAPTCHA solve failed.")
            return False
    except Exception as e:
        logging.error(f"❌ Error solving CAPTCHA: {e}")
        return False

def select_location(driver, location_name):
    try:
        buttons = driver.find_elements(By.XPATH, "//button[contains(text(),'Select Location')]")
        for button in buttons:
            parent = button.find_element(By.XPATH, "./..")
            if location_name in parent.text:
                button.click()
                logging.info(f"✅ Location selected: {location_name}")
                return True
        return False
    except Exception as e:
        logging.error(f"❌ Error selecting location: {e}")
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
        return True
    except Exception as e:
        logging.error(f"❌ Error filling the form: {e}")
        return False

def search_appointments():
    driver = initialize_driver()
    while not status["appointment_found"]:
        for location in preferred_locations:
            try:
                status["current_location"] = location
                driver.get("https://www.dmv.ca.gov/portal/appointments/select-location/S")
                if not select_location(driver, location):
                    continue

                time.sleep(2)
                if find_available_dates(driver):
                    if fill_form(driver):
                        status["appointment_found"] = True
                        driver.quit()
                        return
            except Exception as e:
                logging.error(f"❌ Error during appointment search: {e}")
            time.sleep(120)  # Wait before retrying

# Global variables for status
status = {"current_location": "", "last_checked": "", "appointment_found": False}

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
