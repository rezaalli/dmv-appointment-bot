from flask import Flask, render_template, jsonify, Response
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import threading
import logging
import traceback

app = Flask(__name__)

# Configuration
BASE_URL = "https://www.dmv.ca.gov/portal/appointments/select-appointment-type/"
ZIP_CODE = "92108"
PREFERRED_LOCATIONS = ["San Diego Clairemont", "San Diego", "Chula Vista"]
DATE_RANGE = ("2025-06-03", "2025-06-18")
FORM_DATA = {
    "first_name": "Ashley",
    "last_name": "Barley",
    "email": "barleyohana@gmail.com",
    "phone": "808-927-6227"
}

# Selenium Configuration
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-gpu")

# Logging Configuration
logging.basicConfig(
    filename='dmv_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

# --- STREAMING LOGS ---
def stream_logs():
    def generate():
        with open('dmv_bot.log') as log_file:
            while True:
                line = log_file.readline()
                if line:
                    yield f"data:{line}\n\n"
                time.sleep(1)
    return Response(generate(), mimetype="text/event-stream")

# --- DRIVER INITIALIZATION ---
def initialize_driver():
    logging.info("Starting Chrome Driver")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.set_page_load_timeout(60)
    return driver

# --- MAIN APPOINTMENT BOT ---
def book_appointment():
    while True:
        try:
            logging.info("🚀 Starting Appointment Bot")
            driver = initialize_driver()
            driver.get(BASE_URL)
            time.sleep(2)

            # Step 1: Click "First-time DL Application"
            logging.info("👉 Clicking First-time DL Application")
            driver.find_element(By.LINK_TEXT, "First-time DL Application").click()
            time.sleep(2)

            # Step 2: Click "Get an Appointment"
            logging.info("👉 Selecting 'Get an Appointment'")
            driver.find_element(By.XPATH, "//button[contains(text(), 'Get an Appointment')]").click()
            time.sleep(2)

            # Step 3: Select "REAL ID Driver's License / REAL ID"
            logging.info("👉 Selecting REAL ID option")
            driver.find_element(By.LINK_TEXT, "REAL ID Driver's License / REAL ID").click()
            time.sleep(2)

            # Step 4: Enter ZIP Code and search
            logging.info(f"👉 Entering ZIP code: {ZIP_CODE}")
            zip_input = driver.find_element(By.ID, "office-zip")
            zip_input.send_keys(ZIP_CODE)
            zip_input.send_keys(Keys.RETURN)
            time.sleep(3)

            # Step 5: Attempt to select preferred location
            logging.info("🔎 Searching for preferred location")
            locations = driver.find_elements(By.CLASS_NAME, "location-card")
            success = False
            for location in locations:
                for preferred in PREFERRED_LOCATIONS:
                    if preferred in location.text:
                        logging.info(f"✅ Location found: {preferred}")
                        location.find_element(By.XPATH, ".//button[contains(text(), 'Select Location')]").click()
                        success = True
                        break
                if success:
                    break
            if not success:
                raise Exception("Preferred location not found")

            time.sleep(3)

            # Step 6: Check for available dates
            logging.info("🔍 Scanning for available dates.")
            available_dates = driver.find_elements(By.CLASS_NAME, "date-available")
            date_found = False
            for date in available_dates:
                date_text = date.get_attribute("data-date")
                if DATE_RANGE[0] <= date_text <= DATE_RANGE[1]:
                    logging.info(f"✅ Available date found: {date_text}")
                    date.click()
                    date_found = True
                    break
            if not date_found:
                raise Exception("No dates available within range")

            # Step 7: Fill out the form
            logging.info("📝 Filling out form with user information.")
            driver.find_element(By.ID, "firstName").send_keys(FORM_DATA["first_name"])
            driver.find_element(By.ID, "lastName").send_keys(FORM_DATA["last_name"])
            driver.find_element(By.ID, "email").send_keys(FORM_DATA["email"])
            driver.find_element(By.ID, "phoneNumber").send_keys(FORM_DATA["phone"])
            driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]").click()
            logging.info("🎉 Appointment Successfully Booked!")
            driver.quit()
            return

        except Exception as e:
            logging.error(f"❌ Error Occurred: {str(e)}")
            traceback.print_exc()
            try:
                driver.quit()
            except:
                pass
            logging.info("⏳ Retrying in 30 seconds...")
            time.sleep(30)

# --- FLASK ENDPOINTS ---
@app.route('/')
def home():
    return """
    <h1>DMV Appointment Bot</h1>
    <ul>
        <li><a href="/logs">View Real-time Logs</a></li>
        <li><a href="/status">Check Status</a></li>
    </ul>
    """

@app.route('/logs')
def logs():
    return """
    <h1>Real-time Logs</h1>
    <div id="logs"></div>
    <script>
        const evtSource = new EventSource("/stream");
        evtSource.onmessage = function(event) {
            const newElement = document.createElement("pre");
            newElement.textContent = event.data;
            document.getElementById("logs").appendChild(newElement);
        };
    </script>
    """

@app.route('/stream')
def stream():
    return stream_logs()

@app.route('/status')
def status():
    return jsonify({"status": "Running", "last_checked": time.strftime("%Y-%m-%d %H:%M:%S")})

if __name__ == '__main__':
    threading.Thread(target=book_appointment).start()
    app.run(host='0.0.0.0', port=5000)
