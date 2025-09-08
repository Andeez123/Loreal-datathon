from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scraper.instabot import main
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()
username = os.getenv("insta_username")
password = os.getenv("insta_password")

app = Flask(__name__)

@app.route("/api/health", methods = ['GET'])
def check_status():
    return jsonify({"status": "running", "message": "backend is running"})

@app.route("/api/comment", methods = ['POST'])
def post_scraper():
    data = request.get_json()

    url = data["url"]
    print("Redirecting to website...")

    main(username, password, url)

    return jsonify(200)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)