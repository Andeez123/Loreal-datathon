from transformers import pipeline

# load pretrained spam model
spam_model = pipeline("text-classification",
                      model="unitary/toxic-bert",
                      framework="pt")

def is_spam(comment: str) -> tuple[bool, float]:
    """
    Returns (is_spam, confidence) using enhanced pattern matching
    """
    try:
        comment_lower = comment.lower()
        
        # High-confidence spam patterns (immediate spam classification)
        high_confidence_patterns = [
            "giveaway", "win free", "free prizes", "dm for details", "dm me for",
            "follow for follow", "f4f", "follow back", "follow me back",
            "follow train", "followtrain", "follow4follow",
            "like for like", "l4l", "like4like", "comment for comment", 
            "c4c", "comment4comment", "tag friends", "tag 3 friends",
            "tag someone", "double tap if", "drop a comment if",
            "check out my profile", "check out my page", "visit my profile",
            "boost your followers", "gain followers", "followers fast",
            "collaboration opportunities", "collab", "dm for collab",
            "shop now", "great deals", "amazing deals", "#dmfordeals"
        ]
        
        # Medium-confidence patterns (need multiple matches or context)
        medium_confidence_patterns = [
            "follow me", "support each other", "let's support",
            "keep it up", "amazing content", "#followme", 
            "like this if", "tag a friend", "don't miss out"
        ]
        
        # Check high-confidence patterns first
        high_matches = sum(1 for pattern in high_confidence_patterns if pattern in comment_lower)
        if high_matches >= 1:
            confidence = min(0.95, 0.75 + (high_matches * 0.1))
            return True, confidence
        
        # Check medium-confidence patterns (need multiple or with hashtags)
        medium_matches = sum(1 for pattern in medium_confidence_patterns if pattern in comment_lower)
        hashtag_count = comment.count('#')
        
        # Spam indicators scoring
        spam_score = 0
        
        # Multiple medium patterns
        if medium_matches >= 2:
            spam_score += 2
            
        # Excessive hashtags
        if hashtag_count >= 2:
            spam_score += 1
            
        # Excessive emojis (better emoji detection)
        emoji_patterns = ['🎉', '🚨', '🔥', '💸', '💥', '🎁', '💎', '📈', '🔄', '✨', '🛍️', '💯', '👍', '🙌', '💖', '💬']
        emoji_count = sum(comment.count(emoji) for emoji in emoji_patterns)
        total_emojis = sum(1 for char in comment if ord(char) > 127)  # Better emoji detection
        
        if total_emojis >= 4 or (len(comment) > 0 and total_emojis / len(comment) > 0.15):
            spam_score += 1
            
        # ALL CAPS detection
        if len([c for c in comment if c.isupper()]) > len(comment) * 0.3 and len(comment) > 10:
            spam_score += 1
            
        # Check for promotional language
        promo_words = ['win', 'free', 'prize', 'contest', 'deals', 'sale', 'discount']
        if sum(1 for word in promo_words if word in comment_lower) >= 1 and (hashtag_count >= 1 or total_emojis >= 2):
            spam_score += 2
            
        # Final spam determination
        if spam_score >= 2:
            confidence = min(0.9, 0.6 + (spam_score * 0.1))
            return True, confidence
            
        # Use toxic-bert as additional check for edge cases
        result = spam_model(comment)[0]
        if result["label"] == "TOXIC" and result["score"] > 0.8:
            return True, result["score"]
            
        return False, 0.1  # Low confidence for non-spam
        
    except Exception as e:
        # Fallback to enhanced heuristic if model fails
        spam_keywords = [
            "follow me", "giveaway", "dm for", "follow for follow", "f4f",
            "like for like", "l4l", "tag friends", "check my profile"
        ]
        comment_lower = comment.lower()
        matches = sum(1 for keyword in spam_keywords if keyword in comment_lower)
        is_spam_heuristic = matches >= 1
        confidence = min(0.9, 0.5 + (matches * 0.2)) if is_spam_heuristic else 0.1
        return is_spam_heuristic, confidence