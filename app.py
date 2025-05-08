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

# Global status tracker
status = {
    "current_location": "",
    "last_checked": "",
    "appointment_found": False,
    "last_error": "",
    "retry_count": 0
}

# Setup logging
logging.basicConfig(filename="logs.txt", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# === DRIVER INITIALIZATION ===
def initialize_driver():
    logging.info("🖥️ Initializing Chrome Driver")
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280x1024")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--remote-debugging-port=9222")
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(30)
        logging.info("✅ Chrome Driver initialized successfully")
        return driver
    except Exception as e:
        logging.error(f"🚨 Chrome Driver failed to initialize: {e}")
        status["last_error"] = str(e)
        status["retry_count"] += 1
        if status["retry_count"] >= 3:
            logging.error("🚨 Maximum retry attempts reached. Restarting the bot...")
            status["retry_count"] = 0
        time.sleep(60)
        return initialize_driver()

# === APPOINTMENT SEARCH ===
def search_appointments():
    while not status["appointment_found"]:
        driver = initialize_driver()
        
        for location in preferred_locations:
            try:
                logging.info(f"🌐 Navigating to DMV site for {location}")
                driver.get("https://www.dmv.ca.gov/portal/appointments/select-location/S")
                status["current_location"] = location
                status["last_checked"] = time.strftime("%Y-%m-%d %H:%M:%S")

                # Simulation of form interaction
                logging.info(f"🔎 Searching available dates at {location}")
                
                # Logic for clicking the location, captcha handling, and form filling goes here
                # --- Placeholder for logic ---
                
                # If tab crashes, restart
                if "tab crashed" in driver.page_source.lower():
                    logging.error("🚨 Tab crashed. Restarting browser.")
                    driver.quit()
                    status["retry_count"] += 1
                    if status["retry_count"] >= 3:
                        logging.error("🚨 Maximum retry attempts reached. Restarting the bot...")
                        status["retry_count"] = 0
                    continue

                logging.info(f"✅ Successfully navigated to {location}")
                status["retry_count"] = 0  # Reset retry count after successful navigation

            except Exception as e:
                logging.error(f"❌ Error during appointment search: {e}")
                status["last_error"] = str(e)
                status["retry_count"] += 1
                if status["retry_count"] >= 3:
                    logging.error("🚨 Maximum retry attempts reached. Restarting the bot...")
                    status["retry_count"] = 0
        
        driver.quit()
        time.sleep(120)  # Retry every 2 minutes

# === FLASK ENDPOINTS ===
@app.route('/')
def home():
    return "🎉 DMV Bot is running and searching for appointments!"

@app.route('/status')
def get_status():
    return jsonify(status)

@app.route('/logs')
def get_logs():
    try:
        with open("logs.txt", "r") as file:
            logs = file.read().replace("\n", "<br>")
        return f"<pre>{logs}</pre>"
    except FileNotFoundError:
        return "No logs found."

@app.route('/health')
def health_check():
    if status["last_error"]:
        return jsonify({"status": "unhealthy", "reason": status["last_error"]}), 500
    return jsonify({"status": "healthy"}), 200

def run_bot():
    threading.Thread(target=search_appointments).start()

if __name__ == "__main__":
    run_bot()
    app.run(host="0.0.0.0", port=5000)
