##📊 Instagram Comment Sentiment Analysis Platform

This project is a sentiment analysis platform that extracts comments from Instagram posts and analyzes them using pre-trained NLP models from Hugging Face. It provides insights into the general sentiment (positive, neutral, negative) of an Instagram post.

##Built with:
Selenium → to scrape Instagram comments
Flask → backend framework for API endpoints
SQLite → lightweight database for storing comments & results
Hugging Face Transformers → pre-trained models for sentiment analysis & spam filtering
Postman → API testing and validation

##🚀 Features
🔎 Scrape Instagram comments with Selenium
🗄️ Store comments & results in a local SQLite database
🤖 Run sentiment analysis (positive, neutral, negative) using Hugging Face pre-trained models
🛑 Detect spammy comments with heuristic + model-based filters
🌐 Expose REST API endpoints (Flask) to:
  Fetch stored comments
  Analyze sentiment of comments
  Return aggregated sentiment for an Instagram post

##⚙️ Tech Stack
Backend: Flask
Database: SQLite
ML/NLP: Hugging Face Transformers
Scraping: Selenium
API Testing: Postman

##📡 API Endpoints

##🛠️ Setup Instructions

##🔮 Future Plans
🌐 Chrome Extension: Analyze comments directly while browsing Instagram.
🗄️ Production Database: Move from SQLite → PostgreSQL/MySQL for scalability.
📊 Instagram Business API: Fetch comments directly via API instead of Selenium scraping.
📈 Advanced Analytics: Sentiment trends over time, spam clustering, keyword insights.
