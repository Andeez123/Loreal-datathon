from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

@app.route("/api/health", methods = ['GET'])
def check_status():
    return jsonify({"status": "running", "message": "backend is running"})

@app.route("/api/comment", methods = ['POST'])
def post_scraper():
    data = request.get_json()
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")

    # web driver setup
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    url = data["url"]
    print("Redirecting to website...")
    driver.get(url)

    # wait until comments are visible (adjust xpath if needed)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//ul[contains(@class, 'x78zum5')]//span"))
        )
    except:
        print("Comments not found")
        return jsonify({"error": "No comments loaded"})

    elements = driver.find_elements(By.XPATH, "//ul[contains(@class, 'x78zum5')]//span")
    comments = [el.text for el in elements if el.text.strip()]

    print(comments)

    driver.quit()

    return jsonify({"comments": comments})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)