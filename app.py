# app.py

import os
import time
import logging
from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException

# ========== Flask App Initialization ==========
app = Flask(__name__)

# ========== Logger Setup ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== Health Check ==========
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "Bot is running"}), 200

# ========== Initialize WebDriver ==========
def initialize_driver():
    try:
        logger.info("🟢 Initializing Chrome Driver")
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        logger.info("✅ Driver initialized successfully")
        return driver
    except WebDriverException as e:
        logger.error(f"❌ WebDriver initialization failed: {str(e)}")
        time.sleep(60)
        return initialize_driver()
    except Exception as e:
        logger.error(f"❌ Unexpected error during driver initialization: {str(e)}")
        return None

# ========== DMV Appointment Bot ==========
def start_appointment_bot():
    while True:
        try:
            logger.info("🚀 Starting Appointment Bot")
            driver = initialize_driver()
            if not driver:
                logger.error("❌ Driver failed to initialize. Retrying in 60 seconds...")
                time.sleep(60)
                continue
            
            logger.info("🌐 Navigating to DMV Page")
            driver.get("https://www.dmv.ca.gov/portal/appointments/select-location/A")

            # Wait for page load
            logger.info("⏳ Waiting for page to load completely...")
            time.sleep(10)  # Added buffer time for JavaScript

            # Screenshot for debugging
            driver.save_screenshot('/mnt/data/dmv_screenshot.png')
            logger.info("🖼️ Screenshot saved to /mnt/data/dmv_screenshot.png")

            # Wait for the zip code input field
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "zipCodeInput"))
            )
            logger.info("✅ Page loaded successfully")

            # Enter Zip Code
            zip_code_input = driver.find_element(By.ID, "zipCodeInput")
            zip_code_input.send_keys("92108")
            zip_code_input.submit()
            logger.info("🏷️ Zip Code entered: 92108")

            # Wait for locations to load
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-location-id]"))
            )
            logger.info("✅ Locations loaded")

            # Select preferred location
            preferred_location = driver.find_element(By.CSS_SELECTOR, "button[data-location-id='2']")
            preferred_location.click()
            logger.info("📍 Preferred location selected: San Diego Clairemont")

            # Wait for the appointment page
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "calendar"))
            )
            logger.info("✅ Calendar loaded")

            # Select the first available date
            available_date = driver.find_element(By.CSS_SELECTOR, "button.calendar-date")
            available_date.click()
            logger.info("📅 Available date selected")

            # Fill in the user information
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "firstName"))
            )

            driver.find_element(By.ID, "firstName").send_keys("Ashley")
            driver.find_element(By.ID, "lastName").send_keys("Barley")
            driver.find_element(By.ID, "email").send_keys("barleyohana@gmail.com")
            driver.find_element(By.ID, "phone").send_keys("808-927-6227")
            logger.info("✍️ User information entered successfully")

            # Confirm Appointment
            confirm_button = driver.find_element(By.ID, "confirmAppointment")
            confirm_button.click()
            logger.info("✅ Appointment confirmed successfully!")

            # Close driver
            driver.quit()

            # Break loop after success
            logger.info("🎉 Task completed successfully. Exiting bot.")
            break

        except (NoSuchElementException, TimeoutException) as e:
            logger.error(f"❌ Element not found or timeout: {str(e)}. Retrying in 60 seconds...")
            logger.error(f"🌎 Current URL: {driver.current_url}")
            driver.save_screenshot('/mnt/data/error_screenshot.png')
            logger.info("🖼️ Error screenshot saved to /mnt/data/error_screenshot.png")
            driver.quit()
            time.sleep(60)
        except WebDriverException as e:
            logger.error(f"❌ WebDriver error: {str(e)}. Restarting the driver...")
            driver.quit()
            time.sleep(60)
        except Exception as e:
            logger.error(f"❌ Unknown error occurred: {str(e)}. Retrying in 60 seconds...")
            driver.quit()
            time.sleep(60)

# ========== Start Bot ==========
if __name__ == "__main__":
    logger.info("🌟 DMV Appointment Bot Service Starting...")
    start_appointment_bot()
