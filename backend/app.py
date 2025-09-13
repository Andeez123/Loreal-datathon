from flask import Flask, request, jsonify
from selenium.webdriver.support import expected_conditions as EC
from scraper.instabot import main
from dotenv import load_dotenv
import os
import pandas as pd
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
import json
import json
import sys
from spam_filtering.spam_filter import *
from sentinel_analysis_ai.fastapi_ai_service import *
sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
username = os.getenv("insta_username")
password = os.getenv("insta_password")


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
db = SQLAlchemy(app)
migrate = Migrate(app, db)
CORS(app)

# define models
class postComment(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    post_id = db.Column(db.String(120), nullable = False)
    comment = db.Column(db.String(255))

class Sentiment(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    comment = db.Column(db.String(255))
    label = db.Column(db.String(100))
    confidence = db.Column(db.Float, nullable = False)

class postSentiment(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    post_id = db.Column(db.String(120), nullable = False)
    label = db.Column(db.String(100))


@app.route("/api/health", methods = ['GET'])
def check_status():
    return jsonify({"status": "running", "message": "backend is running"})

# helper function which calls web scraper bot
def insta_scraper(url):
    print("Redirecting to website...")

    main(username, password, url)

    with open('instagram_comments.json', 'r', encoding="utf-8") as file:
            data = json.load(file)
    # print(str(data).encode("cp1252", errors="ignore").decode("cp1252"))
    for entry in data:
        # print(entry["comment"])
        comment_entry = postComment(
            post_id = url,
            comment = entry["comment"]
        )

        db.session.add(comment_entry)
        db.session.commit()

@app.route("/api/comment", methods = ['POST'])
def post_scraper():
    data = request.get_json()
    url = data["url"]
    insta_scraper(url=url)
    return jsonify(200)

# helper function to get comments and return as list 
def fetch_comments(post_id):
    if not post_id:
        return jsonify({"error: post id is required"}, 400)
    
    results = postComment.query.filter_by(post_id=post_id).all()
    return [{"id": r.id, "post_id": r.post_id, "comment": r.comment} for r in results]

@app.route("/api/getcomment", methods = ['GET'])
def get_comments():
    post_id = request.args.get("post_id") # args is a multidict, use dict syntax to query

    comments = fetch_comments(post_id)

    if comments == []:
        return jsonify("no post found", 200)

    return jsonify(comments, 200)

@app.route("/api/filter", methods = ["GET"])
def spam_filter():
    post_id = request.args.get("post_id") # args is a multidict, use dict syntax to query
    
    insta_scraper(post_id)

    comments = fetch_comments(post_id)

    if comments == []:
        return jsonify("no post found", 200)

    results = []
    comment_list = []

    general_sentiment = ""
    negative = 0
    neutral = 0
    positive = 0

    # apply filter to data from database
    filters = ["reply", "replies", "translation", "like", "meta", "instagram"]
    for comment in comments:
        text = comment['comment'].lower()
        if not any(f in text for f in filters):
            comment_list.append(comment['comment'])
    
    for comment in comment_list:
        try:
            # Step 1: Detect language
            detected_language = detect_language(comment)
            logger.info(f"Detected language for '{comment[:30]}...': {detected_language}")
            
            # Step 2: Multilingual spam filter
            spam_detected, spam_confidence = is_multilingual_spam(comment, detected_language)
            if spam_detected:
                results.append({
                    "comment": comment,
                    "label": "spam",
                    "confidence": spam_confidence,
                    "detected_language": detected_language,
                    "model_used": "multilingual_spam_detector"
                })
                continue

            # Step 3: Sentiment analysis
            confidence = 0.5
            label = "neutral"
            model_used = "fallback"
            
            # Try multilingual model first
            if multilingual_sentiment_model:
                try:
                    pred = multilingual_sentiment_model(comment)[0]
                    confidence = float(pred["score"])
                    label = normalize_sentiment_label(pred["label"], confidence)
                    model_used = "multilingual-bert"
                except Exception as e:
                    logger.warning(f"Multilingual model failed: {e}")
            
            # If multilingual failed or confidence low, try English model for English text
            if (confidence < 0.7 and detected_language == "en" and english_sentiment_model):
                try:
                    pred = english_sentiment_model(comment)[0]
                    eng_confidence = float(pred["score"])
                    eng_label = normalize_sentiment_label(pred["label"], eng_confidence)
                    
                    if eng_confidence > confidence:
                        confidence = eng_confidence
                        label = eng_label
                        model_used = "english-roberta"
                except Exception as e:
                    logger.warning(f"English model failed: {e}")
            
            # Apply confidence threshold
            if confidence < 0.6:
                final_label = "neutral"
            else:
                final_label = label

            results.append({
                "comment": comment,
                "label": final_label,
                "confidence": confidence,
                "detected_language": detected_language,
                "model_used": model_used
            })
            
        except Exception as e:
            logger.error(f"Error analyzing comment '{comment}': {e}")
            # Fallback result
            results.append({
                "comment": comment,
                "label": "neutral",
                "confidence": 0.5,
                "detected_language": "unknown",
                "model_used": "error_fallback"
            })

    for result in results:
        label = result['label']
        if label == "negative":
            negative += 1
        elif label == "neutral":
            neutral += 1
        elif label == "positive":
            positive += 1

    if (positive > negative) and (neutral > negative):
        print(f"positive: {positive}")
        print(f"neutral: {neutral}")
        print(f"negative: {negative}")
        general_sentiment = "positive"
    elif (negative > positive):
        general_sentiment = "negative"
    
    return jsonify({"general_sentiment": general_sentiment}), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)

    