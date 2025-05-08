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

# Setup logging to a file and console
logging.basicConfig(
    filename="logs.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

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

def initialize_driver():
    logging.info("🖥️ Initializing Chrome Driver")
    
    chrome_options = webdriver.ChromeOptions()
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
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-client-side-phishing-detection")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--remote-debugging-port=9222")
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.set_page_load_timeout(30)
        driver.maximize_window()
        return driver
    except Exception as e:
        logging.error(f"🚨 Chrome Driver failed to initialize: {e}")
        status["last_error"] = str(e)

def search_appointments():
    while not status["appointment_found"]:
        driver = initialize_driver()
        if not driver:
            time.sleep(60)
            continue
        
        for location in preferred_locations:
            try:
                driver.get("https://www.dmv.ca.gov/portal/appointments/select-location/S")
                logging.info(f"🌐 Navigated to DMV Site: {location}")
                # Add location search logic here
                time.sleep(2)
                
                # If tab crashes, retry
                if "tab crashed" in driver.page_source.lower():
                    logging.error("🚨 Tab crashed. Restarting browser.")
                    driver.quit()
                    driver = initialize_driver()
                    continue

            except Exception as e:
                logging.error(f"❌ Error during appointment search: {e}")
                status["last_error"] = str(e)
        
        driver.quit()
        time.sleep(120)

# Flask Endpoints
@app.route('/')
def home():
    return "🎉 DMV Bot is running and searching for appointments!"

@app.route('/status')
def get_status():
    return jsonify(status)

@app.route('/logs')
def get_logs():
    with open("logs.txt", "r") as file:
        logs = file.read().replace("\n", "<br>")
    return f"<pre>{logs}</pre>"

def run_bot():
    threading.Thread(target=search_appointments).start()

if __name__ == "__main__":
    run_bot()
    app.run(host="0.0.0.0", port=5000)
