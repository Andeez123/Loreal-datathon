## Instagram Comment Sentiment Analysis Platform

This project is a sentiment analysis platform that extracts comments from Instagram posts and analyzes them using pre-trained NLP models from Hugging Face. It provides insights into the general sentiment (positive, neutral, negative) of an Instagram post.

## Built with:
- Selenium → to scrape Instagram comments
- Flask → backend framework for API endpoints
- SQLite → lightweight database for storing comments & results
- Hugging Face Transformers → pre-trained models for sentiment analysis & spam filtering
- Postman → API testing and validation

## Features
- Scrape Instagram comments with Selenium
- Store comments & results in a local SQLite database
- Run sentiment analysis (positive, neutral, negative) using Hugging Face pre-trained models
- Detect spammy comments with heuristic + model-based filters
- Expose REST API endpoints (Flask) to:
  - Fetch stored comments
  - Analyze sentiment of comments
  - Return aggregated sentiment for an Instagram post

## Tech Stack
- Backend: Flask
- Database: SQLite
- ML/NLP: Hugging Face Transformers
- Scraping: Selenium
- API Testing: Postman

## API Endpoints
- /api/health
  - used to check status of backend server
- /api/comment (HTTP POST)
  - accepts an Instagram link, scrapes comments and saves to local database
- /api/getcomment (HTTP GET)
  - accepts an Instagram link, and returns comments related to the post
- /api/filter (HTTP GET)
  - accepts an Instagram link, passes the comments data to local NLP models and returns a generalised sentiment of the Instagram post

## Setup Instructions
1. Clone the repository to your local machine
2. In the project ROOT directory, create a .env file, and insert your Instagram credentials as such:
  insta_username = "your username"
  insta_password = "your password"
3. If you prefer, create a virtual env and download the required packages using:
  ```
  pip install -r requirements.txt
  ```
4. Once the required dependencies are installed, run the backend by doing:
  ```
  cd backend
  python app.py
  ```
5. Once the backend is running, the frontend can be run using:
  ```
  cd fontend
  npm run dev
  ```

## Future Plans
- Chrome Extension: Analyze comments directly while browsing Instagram.
- Production Database: Move from SQLite → PostgreSQL/MySQL for scalability.
- Instagram Business API: Fetch comments directly via API instead of Selenium scraping.

