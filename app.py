from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import random
import time

app = Flask(__name__)

# Global Configurations
PROXY_LIST = [
    "35.86.81.136:3128",
    "18.132.36.51:3128",
    "80.1.215.23:8888",
    "13.126.217.46:3128",
    "119.156.195.173:3128"
]

DMV_URL = "https://www.dmv.ca.gov/portal/appointments/select-location/A"

# Initialize Chrome Driver
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--window-size=1920,1080")

    # Set up proxy
    proxy = get_working_proxy()
    if proxy:
        chrome_options.add_argument(f'--proxy-server={proxy}')
        print(f"🌐 Using Proxy: {proxy}")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(60)
    return driver

# Get a working proxy
def get_working_proxy():
    print("🔄 Rotating through proxies...")
    for proxy in PROXY_LIST:
        if is_proxy_alive(proxy):
            print(f"✅ Proxy working: {proxy}")
            return proxy
    print("❌ No working proxies found.")
    return None

# Verify if a proxy is alive
def is_proxy_alive(proxy):
    try:
        response = requests.get("https://www.dmv.ca.gov", proxies={"http": proxy, "https": proxy}, timeout=5)
        if response.status_code == 200:
            return True
    except Exception as e:
        print(f"⚠️ Proxy failed: {proxy} - {str(e)}")
    return False

# Wait for an element to load
def wait_for_element(driver, xpath, timeout=30):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return element
    except Exception as e:
        print(f"🔴 Element not found: {xpath}. Retrying...")
        driver.save_screenshot("/mnt/data/page_load_error.png")
        return None

# Main Bot Logic
def main_loop():
    while True:
        print("🚀 Starting Appointment Bot")
        driver = init_driver()
        
        try:
            print("🌐 Navigating to DMV Page")
            driver.get(DMV_URL)

            # Check if the page loaded properly
            if not wait_for_element(driver, "//h1[contains(text(), 'Which office would you like to visit?')]"):
                print("❌ Critical error: Page did not load properly.")
                driver.quit()
                continue

            print("✅ Page loaded successfully, proceeding...")
            # Insert further navigation and interaction logic here...

        except Exception as e:
            print(f"❌ Error during execution: {str(e)}")
        finally:
            driver.quit()
            print("🔄 Restarting in 60 seconds...")
            time.sleep(60)

# Start the Flask app
@app.route('/start', methods=['GET'])
def start_bot():
    try:
        main_loop()
        return jsonify({"status": "Bot started successfully"}), 200
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
