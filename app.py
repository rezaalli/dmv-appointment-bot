from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from anticaptchaofficial.imagecaptcha import imagecaptcha
import chromedriver_autoinstaller
import time
import base64
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, jsonify
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import random

# --- Configuration ---
first_name = "Ashley"
last_name = "Barley"
phone_number = "808-927-6227"
email_address = os.getenv('NOTIFICATION_EMAIL')
preferred_locations = ["San Diego Clairemont", "San Diego", "Chula Vista"]
captcha_api_key = os.getenv('CAPTCHA_API_KEY')
date_range = list(range(3, 19))  # June 3 to June 18
primary_zip_code = "92108"
dmv_url = "https://www.dmv.ca.gov/portal/appointments/select-location/S"

# --- Flask App ---
app = Flask(__name__)
search_status = {
    "location": None,
    "status": "Idle",
    "last_checked": None,
    "captcha_solved": False,
    "appointment_found": False
}

@app.route('/')
def index():
    return "DMV Bot is running!"

@app.route('/status')
def status():
    return jsonify(search_status)

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Anti-Captcha Solver ---
solver = imagecaptcha()
solver.set_verbose(1)
solver.set_key(captcha_api_key)

# --- Initialize WebDriver ---
def initialize_driver():
    chromedriver_autoinstaller.install()
    driver = webdriver.Chrome()
    driver.maximize_window()
    driver.get(dmv_url)
    return driver

# --- CAPTCHA Solver ---
def solve_captcha(driver):
    try:
        search_status['captcha_solved'] = False
        logging.info("⚠️ CAPTCHA detected, solving...")
        captcha_image = driver.find_element(By.CSS_SELECTOR, "img.captcha-image-selector")  
        captcha_image.screenshot("captcha.png")
        result = solver.solve_and_return_solution("captcha.png")
        if result != 0:
            logging.info(f"✅ CAPTCHA Solved: {result}")
            captcha_input = driver.find_element(By.ID, 'captcha-input-id')  
            captcha_input.send_keys(result)
            search_status['captcha_solved'] = True
            return True
        else:
            logging.error("❌ CAPTCHA solve failed.")
            return False
    except Exception as e:
        logging.error(f"CAPTCHA error: {e}")
        return False

# --- Main Loop with Thread Pool and Exponential Backoff ---
def main_loop():
    with ThreadPoolExecutor(max_workers=len(preferred_locations)) as executor:
        futures = {executor.submit(initialize_driver): loc for loc in preferred_locations}
        for future in as_completed(futures):
            location = futures[future]
            driver = future.result()
            for attempt in range(5):
                if solve_captcha(driver):
                    search_status['location'] = location
                    search_status['status'] = 'Running'
                    if find_available_dates(driver):
                        search_status['status'] = 'Appointment Found'
                        return
                time.sleep(2 ** attempt + random.uniform(0, 1))
            driver.quit()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
    main_loop()
