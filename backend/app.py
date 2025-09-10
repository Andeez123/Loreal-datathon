from flask import Flask, request, jsonify
from selenium.webdriver.support import expected_conditions as EC
from scraper.instabot import main
from dotenv import load_dotenv
import os
import pandas as pd
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import json
import json
import sys
from spam_filtering.spam_filter import *
sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
username = os.getenv("insta_username")
password = os.getenv("insta_password")


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
db = SQLAlchemy(app)
migrate = Migrate(app, db)

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


@app.route("/api/health", methods = ['GET'])
def check_status():
    return jsonify({"status": "running", "message": "backend is running"})

@app.route("/api/comment", methods = ['POST'])
def post_scraper():
    data = request.get_json()

    url = data["url"]
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

    return jsonify(200)

def fetch_comments(post_id):
    if not post_id:
        return jsonify({"error: post id is required"}, 400)
    
    results = postComment.query.filter_by(post_id=post_id).all()
    return [{"id": r.id, "post_id": r.post_id, "comment": r.comment} for r in results]

@app.route("/api/getcomment", methods = ['GET'])
def get_comments():
    post_id = request.args.get("post_id") # args is a multidict, use dict syntax to query

    comments = fetch_comments(post_id)

    return jsonify(comments, 200)

@app.route("/api/filter", methods = ["POST"])
def spam_filter():
    post_id = request.args.get("post_id") # args is a multidict, use dict syntax to query

    comments = fetch_comments(post_id)
    results = []
    comment_list = []

    # apply filter to data from database
    filters = ["reply", "replies", "translation", "like", "meta", "instagram"]
    for comment in comments:
        text = comment['comment'].lower()
        if not any(f in text for f in filters):
            comment_list.append(comment['comment'])
    
    print(comment_list)
    return jsonify(comment_list, 200)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)

    