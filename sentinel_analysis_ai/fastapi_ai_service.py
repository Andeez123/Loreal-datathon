from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from transformers import pipeline

# -------------------
# Load Pre-trained Models
# -------------------
# Sentiment model (short text, slang-friendly)
sentiment_model = pipeline("sentiment-analysis", 
                           model="cardiffnlp/twitter-roberta-base-sentiment",
                           framework="pt")

# Spam detection model (trained on social media spam)
spam_model = pipeline("text-classification",
                      model="unitary/toxic-bert",
                      framework="pt")

# Map CardiffNLP labels to readable ones
label_map = {
    "LABEL_0": "negative",
    "LABEL_1": "neutral", 
    "LABEL_2": "positive"
}

# ML-based spam detection
def is_spam(comment: str) -> tuple[bool, float]:
    """
    Returns (is_spam, confidence) using ML model
    """
    try:
        # Use toxic-bert as a proxy for spam detection
        # Toxic content often correlates with spam on social media
        result = spam_model(comment)[0]
        
        # If the model predicts TOXIC with high confidence, consider it spam
        if result["label"] == "TOXIC" and result["score"] > 0.7:
            return True, result["score"]
        
        # Additional heuristic checks for Instagram-specific spam patterns
        comment_lower = comment.lower()
        instagram_spam_patterns = [
            "follow me", "follow back", "f4f", "follow for follow",
            "giveaway", "free", "win", "prize", "contest",
            "dm me", "dm for", "check dm", "inbox me",
            "link in bio", "click link", "swipe up",
            "buy now", "discount", "sale", "promo code",
            "gain followers", "followers fast", "instagram followers",
            "like for like", "l4l", "comment4comment", "c4c",
            "bot", "auto follow", "follow train"
        ]
        
        spam_score = sum(1 for pattern in instagram_spam_patterns if pattern in comment_lower)
        spam_confidence = min(0.95, 0.3 + (spam_score * 0.2))  # Scale confidence based on matches
        
        if spam_score >= 2:  # If 2+ spam patterns detected
            return True, spam_confidence
            
        # Check for excessive emojis (spam indicator)
        emoji_count = sum(1 for char in comment if ord(char) > 0x1F600)
        if len(comment) > 0 and emoji_count / len(comment) > 0.3:  # >30% emojis
            return True, 0.8
            
        return False, 1.0 - spam_confidence
        
    except Exception as e:
        # Fallback to simple heuristic if model fails
        spam_keywords = ["follow me", "giveaway", "dm for collab", "http", "buy now"]
        comment_lower = comment.lower()
        is_spam_heuristic = any(keyword in comment_lower for keyword in spam_keywords)
        return is_spam_heuristic, 0.7

# -------------------
# FastAPI Setup
# -------------------
app = FastAPI(title="Instagram Comment Sentiment API")

# Input schema
class CommentRequest(BaseModel):
    post_id: str
    comments: List[str]

# Output schema
class CommentResult(BaseModel):
    comment: str
    label: str
    confidence: float

# -------------------
# Routes
# -------------------
@app.post("/analyze", response_model=List[CommentResult])
def analyze_comments(request: CommentRequest):
    results = []

    for comment in request.comments:
        # Step 1: Spam filter
        spam_detected, spam_confidence = is_spam(comment)
        if spam_detected:
            results.append({
                "comment": comment,
                "label": "spam",
                "confidence": spam_confidence
            })
            continue

        # Step 2: Sentiment analysis
        pred = sentiment_model(comment)[0]
        raw_label = pred["label"]  # This will be "LABEL_0", "LABEL_1", or "LABEL_2"
        confidence = float(pred["score"])
        
        # Map to readable label
        mapped_label = label_map.get(raw_label, "neutral")

        # Apply a neutral threshold: if confidence is below 0.6, label as neutral
        if confidence < 0.5:  # uncertain prediction
            final_label = "neutral"
        else:
            final_label = mapped_label

        results.append({
            "comment": comment,
            "label": final_label,
            "confidence": confidence
        })

    return results

# -------------------
# Run server (dev mode)
# -------------------
# uvicorn filename:app --reload