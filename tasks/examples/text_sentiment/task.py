"""
Text Sentiment Analysis Task - NLP Example
"""
import re
from typing import Any, List, Dict
from tasks.base.task_base import MLTask


class Task(MLTask):
    """Text sentiment analysis using rule-based approach and keyword matching"""
    
    def __init__(self):
        super().__init__()
        self.positive_words = set()
        self.negative_words = set()
        self.intensifiers = set()
        self.negations = set()
    
    def load_model(self):
        """Load sentiment lexicon and rules"""
        self.log_info("Loading sentiment analysis model...")
        
        # Simple sentiment lexicons (in production, use more comprehensive ones)
        self.positive_words = {
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 
            'love', 'like', 'enjoy', 'happy', 'pleased', 'satisfied', 'awesome',
            'brilliant', 'perfect', 'outstanding', 'superb', 'magnificent',
            'delighted', 'thrilled', 'excited', 'positive', 'beautiful'
        }
        
        self.negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'angry',
            'sad', 'disappointed', 'frustrated', 'annoying', 'boring', 'worst',
            'disgusting', 'pathetic', 'useless', 'failure', 'problem', 'issue',
            'negative', 'poor', 'weak', 'inferior', 'inadequate', 'unacceptable'
        }
        
        self.intensifiers = {
            'very', 'extremely', 'really', 'quite', 'absolutely', 'totally',
            'completely', 'highly', 'incredibly', 'remarkably', 'exceptionally'
        }
        
        self.negations = {
            'not', 'no', 'never', 'nothing', 'nowhere', 'nobody', 'none',
            'neither', 'without', 'hardly', 'scarcely', 'barely'
        }
        
        self.log_info("Sentiment model loaded successfully")
        return True
    
    def predict(self, preprocessed_input: str) -> Dict[str, Any]:
        """Analyze sentiment of text"""
        self.log_info("Running sentiment analysis...")
        
        # Tokenize text
        words = self.preprocess_text(preprocessed_input)
        
        # Calculate sentiment scores
        positive_score = 0
        negative_score = 0
        word_count = len(words)
        
        # Analyze words with context
        for i, word in enumerate(words):
            # Check for negation in previous words
            is_negated = self._check_negation(words, i)
            
            # Check for intensifier in previous word
            intensifier_multiplier = self._check_intensifier(words, i)
            
            # Calculate word sentiment
            word_sentiment = 0
            if word in self.positive_words:
                word_sentiment = 1 * intensifier_multiplier
            elif word in self.negative_words:
                word_sentiment = -1 * intensifier_multiplier
            
            # Apply negation
            if is_negated:
                word_sentiment *= -1
            
            # Add to scores
            if word_sentiment > 0:
                positive_score += word_sentiment
            elif word_sentiment < 0:
                negative_score += abs(word_sentiment)
        
        # Normalize scores
        total_sentiment_words = positive_score + negative_score
        if total_sentiment_words > 0:
            positive_ratio = positive_score / total_sentiment_words
            negative_ratio = negative_score / total_sentiment_words
        else:
            positive_ratio = 0
            negative_ratio = 0
        
        # Determine overall sentiment
        net_score = positive_score - negative_score
        
        if net_score > 0:
            sentiment = "positive"
            confidence = positive_ratio
        elif net_score < 0:
            sentiment = "negative"
            confidence = negative_ratio
        else:
            sentiment = "neutral"
            confidence = 1.0 - max(positive_ratio, negative_ratio)
        
        # Ensure confidence is reasonable
        confidence = max(0.5, min(1.0, confidence)) if sentiment != "neutral" else 0.5
        
        self.log_info(f"Sentiment analysis completed: {sentiment} ({confidence:.2f})")
        
        return {
            "sentiment": sentiment,
            "confidence": float(confidence),
            "scores": {
                "positive": float(positive_score),
                "negative": float(negative_score),
                "net": float(net_score)
            },
            "statistics": {
                "word_count": word_count,
                "sentiment_words": int(total_sentiment_words),
                "positive_words": int(positive_score),
                "negative_words": int(negative_score)
            }
        }
    
    def preprocess_input(self, input_data: Any) -> str:
        """Preprocess text input"""
        self.log_info("Preprocessing text input...")
        
        if isinstance(input_data, str):
            text = input_data
        elif isinstance(input_data, dict) and 'text' in input_data:
            text = input_data['text']
        elif isinstance(input_data, dict) and 'message' in input_data:
            text = input_data['message']
        else:
            raise ValueError("Input must be string or dict with 'text'/'message' field")
        
        # Basic text cleaning
        text = text.strip()
        if not text:
            raise ValueError("Input text cannot be empty")
        
        self.log_info(f"Text preprocessed: {len(text)} characters")
        return text
    
    def preprocess_text(self, text: str) -> List[str]:
        """Preprocess text into words"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:]', ' ', text)
        
        # Tokenize
        words = text.split()
        
        # Remove empty strings
        words = [word.strip('.,!?;:') for word in words if word.strip()]
        
        return words
    
    def _check_negation(self, words: List[str], current_index: int) -> bool:
        """Check if current word is negated by previous words"""
        # Look back up to 3 words for negation
        start_index = max(0, current_index - 3)
        for i in range(start_index, current_index):
            if words[i] in self.negations:
                return True
        return False
    
    def _check_intensifier(self, words: List[str], current_index: int) -> float:
        """Check if current word is intensified by previous word"""
        if current_index > 0 and words[current_index - 1] in self.intensifiers:
            return 1.5  # Multiply sentiment by 1.5 for intensifiers
        return 1.0
    
    def postprocess_output(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Postprocess sentiment analysis results"""
        self.log_info("Postprocessing sentiment results...")
        
        result = {
            "task_id": self._task_id,
            "task_type": "sentiment_analysis",
            "timestamp": self._get_timestamp(),
            **output_data
        }
        
        # Add interpretation
        sentiment = output_data["sentiment"]
        confidence = output_data["confidence"]
        
        if confidence >= 0.8:
            strength = "strong"
        elif confidence >= 0.6:
            strength = "moderate"
        else:
            strength = "weak"
        
        result["interpretation"] = {
            "sentiment_label": sentiment,
            "strength": strength,
            "description": f"{strength.capitalize()} {sentiment} sentiment",
            "recommendation": self._get_recommendation(sentiment, confidence)
        }
        
        return result
    
    def _get_recommendation(self, sentiment: str, confidence: float) -> str:
        """Get recommendation based on sentiment"""
        if sentiment == "positive" and confidence >= 0.7:
            return "This is positive feedback - consider highlighting or sharing"
        elif sentiment == "negative" and confidence >= 0.7:
            return "This is negative feedback - may require attention or response"
        elif sentiment == "neutral":
            return "Neutral sentiment detected - monitor for changes"
        else:
            return "Low confidence prediction - consider manual review"
    
    def validate_input(self, input_data: Any) -> bool:
        """Validate input data"""
        if isinstance(input_data, str):
            return len(input_data.strip()) > 0
        elif isinstance(input_data, dict):
            return ('text' in input_data and input_data['text']) or \
                   ('message' in input_data and input_data['message'])
        return False
    
    def get_requirements(self) -> List[str]:
        """Get required packages"""
        return []  # Only uses built-in Python libraries
    
    def get_info(self) -> Dict[str, Any]:
        """Get task information"""
        return {
            **super().get_info(),
            "description": "Text sentiment analysis using rule-based approach",
            "input_formats": [
                "Text string",
                "Dict with 'text' or 'message' field"
            ],
            "output_format": {
                "sentiment": "Predicted sentiment (positive, negative, neutral)",
                "confidence": "Confidence score (0.0 to 1.0)",
                "scores": "Detailed positive/negative/net scores",
                "statistics": "Word count and sentiment word statistics"
            },
            "model_type": "Rule-based with lexicon",
            "supported_languages": ["English"],
            "lexicon_size": {
                "positive_words": len(self.positive_words),
                "negative_words": len(self.negative_words)
            }
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()