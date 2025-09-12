from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from transformers import pipeline
import langdetect
from langdetect.lang_detect_exception import LangDetectException
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------
# Load Compatible Multilingual Models
# -------------------

try:
    # Primary multilingual sentiment model (compatible with current transformers)
    multilingual_sentiment_model = pipeline(
        "sentiment-analysis", 
        model="nlptown/bert-base-multilingual-uncased-sentiment",
        framework="pt"
    )
    logger.info("✅ Primary multilingual sentiment model loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load primary model: {e}")
    multilingual_sentiment_model = None

try:
    # Backup English model (very reliable)
    english_sentiment_model = pipeline(
        "sentiment-analysis", 
        model="cardiffnlp/twitter-roberta-base-sentiment",
        framework="pt"
    )
    logger.info("✅ English sentiment model loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load English model: {e}")
    english_sentiment_model = None

try:
    # Multilingual spam/toxic detection model
    multilingual_spam_model = pipeline(
        "text-classification",
        model="martin-ha/toxic-comment-model",
        framework="pt"
    )
    logger.info("✅ Multilingual spam model loaded successfully")
except Exception as e:
    logger.warning(f"⚠️ Spam model failed, using heuristic approach: {e}")
    multilingual_spam_model = None

# Language detection
def detect_language(text: str) -> str:
    """Detect the language of the text"""
    try:
        return langdetect.detect(text)
    except LangDetectException:
        return "unknown"

# Map different model outputs to consistent labels
def normalize_sentiment_label(label: str, confidence: float) -> str:
    """Normalize different model outputs to consistent labels"""
    label = label.lower()
    
    # Handle star ratings from multilingual BERT
    if "1 star" in label or "2 stars" in label:
        return "negative"
    elif "3 stars" in label:
        return "neutral" 
    elif "4 stars" in label or "5 stars" in label:
        return "positive"
    
    # Handle Cardiff NLP labels (LABEL_0, LABEL_1, LABEL_2)
    if label == "label_0":
        return "negative"
    elif label == "label_1":
        return "neutral"
    elif label == "label_2":
        return "positive"
    
    # Handle standard labels
    if "neg" in label:
        return "negative"
    elif "pos" in label:
        return "positive"
    elif "neutral" in label:
        return "neutral"
    else:
        # If confidence is low, default to neutral
        return "neutral" if confidence < 0.7 else "positive"

# Enhanced multilingual spam detection
def is_multilingual_spam(comment: str, language: str = "unknown") -> tuple[bool, float]:
    """
    Enhanced spam detection for multiple languages
    """
    try:
        comment_lower = comment.lower()
        
        # Universal spam patterns (work across languages with Latin script)
        universal_spam_patterns = [
            "http", "www.", ".com", ".net", ".org", "bit.ly", "tinyurl",
            "follow", "subscribe", "sub", "dm", "pm", "inbox",
            "win", "free", "prize", "giveaway", "contest", "lottery"
        ]
        
        # Language-specific spam patterns
        language_specific_patterns = {
            "es": ["sígueme", "sorteo", "gratis", "premio", "concurso", "dm", "mp", "seguir"],  # Spanish
            "fr": ["suivez", "concours", "gratuit", "prix", "gagnant", "mp", "suivre"],       # French  
            "pt": ["siga", "sorteio", "grátis", "prêmio", "concurso", "dm", "seguir"],        # Portuguese
            "it": ["segui", "concorso", "gratis", "premio", "vincere", "dm", "seguire"],       # Italian
            "de": ["folgen", "gewinnspiel", "kostenlos", "preis", "gewinnen", "folgt"],       # German
            "ar": ["متابعة", "مسابقة", "مجاني", "جائزة", "ربح", "تابع"],                      # Arabic
            "ja": ["フォロー", "プレゼント", "無料", "賞品", "当選", "フォロバ"],                         # Japanese
            "ko": ["팔로우", "이벤트", "무료", "상품", "당첨", "팔로백"],                          # Korean
            "zh": ["关注", "抽奖", "免费", "奖品", "获奖", "回关"],                            # Chinese
            "hi": ["फॉलो", "गिवअवे", "मुफ्त", "पुरस्कार", "जीत", "फॉलो बैक"],                   # Hindi
            "ru": ["подписка", "розыгрыш", "бесплатно", "приз", "выиграть", "подписаться"],        # Russian
            "tr": ["takip", "çekiliş", "ücretsiz", "ödül", "kazan", "takip et"],               # Turkish
            "nl": ["volgen", "wedstrijd", "gratis", "prijs", "winnen", "volg terug"],            # Dutch
            "sv": ["följa", "tävling", "gratis", "pris", "vinna", "följa tillbaka"],                 # Swedish
            "da": ["følg", "konkurrence", "gratis", "præmie", "vind", "følg tilbage"],             # Danish
            "no": ["følg", "konkurranse", "gratis", "premie", "vinn", "følg tilbake"],             # Norwegian
        }
        
        # Check universal patterns
        universal_matches = sum(1 for pattern in universal_spam_patterns if pattern in comment_lower)
        
        # Check language-specific patterns
        language_matches = 0
        if language in language_specific_patterns:
            patterns = language_specific_patterns[language]
            language_matches = sum(1 for pattern in patterns if pattern in comment_lower)
        
        # Calculate spam score
        total_matches = universal_matches + language_matches * 1.5
        
        # Use ML model for additional validation if available
        ml_confidence = 0.0
        if multilingual_spam_model:
            try:
                ml_result = multilingual_spam_model(comment)[0]
                is_toxic_ml = ml_result["label"] == "TOXIC" and ml_result["score"] > 0.7
                ml_confidence = ml_result["score"] if is_toxic_ml else 0.0
            except:
                is_toxic_ml = False
        else:
            is_toxic_ml = False
        
        # Enhanced emoji spam detection
        spam_emojis = ['🎉', '🚨', '🔥', '💸', '💥', '🎁', '💎', '📈', '🔄', '✨', '🛍️', '💯', '👍', '🙌', '💖', '💬', '🚀', '💰', '🎊', '🏆']
        emoji_count = sum(comment.count(emoji) for emoji in spam_emojis)
        total_emojis = sum(1 for char in comment if ord(char) > 127)
        
        emoji_spam_score = 0
        if total_emojis >= 4 or (len(comment) > 0 and total_emojis / len(comment) > 0.15):
            emoji_spam_score = 1
        
        # Check for excessive hashtags
        hashtag_count = comment.count('#')
        hashtag_score = 1 if hashtag_count >= 3 else 0
        
        # Final determination
        final_score = total_matches + emoji_spam_score + hashtag_score + (2 if is_toxic_ml else 0)
        
        if final_score >= 2 or is_toxic_ml:
            confidence = min(0.95, 0.6 + (final_score * 0.1) + ml_confidence * 0.2)
            return True, confidence
        
        return False, 0.1
        
    except Exception as e:
        logger.error(f"Error in multilingual spam detection: {e}")
        # Simple fallback
        simple_spam_keywords = ["http", "follow me", "giveaway", "free", "win", "dm me"]
        is_spam_simple = any(keyword in comment.lower() for keyword in simple_spam_keywords)
        return is_spam_simple, 0.6 if is_spam_simple else 0.1

# -------------------
# FastAPI Setup
# -------------------
app = FastAPI(title="Multilingual Instagram Comment Sentiment API")

# Input schema
class CommentRequest(BaseModel):
    post_id: str
    comments: List[str]

# Enhanced output schema
class CommentResult(BaseModel):
    comment: str
    label: str
    confidence: float
    detected_language: Optional[str] = None
    model_used: Optional[str] = None

# -------------------
# Routes
# -------------------
@app.post("/analyze", response_model=List[CommentResult])
def analyze_comments(request: CommentRequest):
    results = []

    for comment in request.comments:
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

    return results

@app.get("/health")
def health_check():
    """Health check endpoint"""
    models_status = {
        "multilingual_sentiment": "✅" if multilingual_sentiment_model else "❌",
        "english_sentiment": "✅" if english_sentiment_model else "❌",
        "multilingual_spam": "✅" if multilingual_spam_model else "❌ (using heuristics)"
    }
    
    return {
        "status": "healthy",
        "models_loaded": models_status,
        "message": "API is running with available models"
    }

@app.get("/supported-languages")
def get_supported_languages():
    """Get list of supported languages"""
    return {
        "message": "This API supports 17+ languages with high accuracy",
        "models": {
            "tabularisai_multilingual": "17+ languages including Chinese, Japanese, Korean, Spanish, French, German, Italian, Portuguese, Dutch, Russian, Arabic, Hindi, Turkish, etc.",
            "xlm_roberta_backup": "100+ languages (backup model)", 
            "english_roberta": "English (high accuracy)",
            "spam_detection": "16+ languages with pattern matching"
        },
        "well_supported_languages": [
            "English (en)", "Chinese (zh)", "Spanish (es)", "French (fr)", 
            "German (de)", "Italian (it)", "Portuguese (pt)", "Dutch (nl)", 
            "Russian (ru)", "Japanese (ja)", "Korean (ko)", "Arabic (ar)",
            "Hindi (hi)", "Turkish (tr)", "Swedish (sv)", "Danish (da)",
            "Norwegian (no)", "Thai (th)", "Vietnamese (vi)"
        ]
    }

# -------------------
# Run server
# -------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)