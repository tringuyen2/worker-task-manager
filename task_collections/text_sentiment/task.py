# tasks/text_sentiment/task.py
import re
from typing import List, Any, Dict
import os
import sys
from abc import ABC, abstractmethod

# BaseTask class definition (copied to avoid import issues)
class BaseTask(ABC):
    """Base class cho tất cả AI tasks"""
    
    def __init__(self):
        self.task_name = self.__class__.__name__
        
    @abstractmethod
    def process(self, input_data: Any) -> Any:
        """Xử lý input và trả về kết quả"""
        pass
    
    @abstractmethod
    def get_requirements(self) -> List[str]:
        """Trả về list các thư viện cần thiết"""
        pass
    
    def get_description(self) -> str:
        """Mô tả task"""
        return f"AI Task: {self.task_name}"

class TextSentimentTask(BaseTask):
    """Text Sentiment Analysis using simple word-based approach"""
    
    def __init__(self):
        super().__init__()
        self.positive_words = [
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 
            'awesome', 'brilliant', 'perfect', 'love', 'like', 'happy', 'joy',
            'beautiful', 'best', 'incredible', 'outstanding', 'superb'
        ]
        self.negative_words = [
            'bad', 'terrible', 'awful', 'horrible', 'disgusting', 'hate', 
            'dislike', 'angry', 'sad', 'disappointed', 'frustrated', 'annoying',
            'worst', 'pathetic', 'useless', 'boring', 'stupid', 'ridiculous'
        ]
        print("Sentiment analysis model initialized")
    
    def _preprocess_text(self, text: str) -> List[str]:
        """Preprocess text for analysis"""
        # Convert to lowercase and remove punctuation
        text = re.sub(r'[^\w\s]', '', text.lower())
        words = text.split()
        return words
    
    def _calculate_sentiment(self, words: List[str]) -> Dict[str, Any]:
        """Calculate sentiment score"""
        positive_score = sum(1 for word in words if word in self.positive_words)
        negative_score = sum(1 for word in words if word in self.negative_words)
        
        total_words = len(words)
        neutral_score = total_words - positive_score - negative_score
        
        # Calculate overall sentiment
        if positive_score > negative_score:
            sentiment = 'positive'
            confidence = (positive_score - negative_score) / total_words if total_words > 0 else 0
        elif negative_score > positive_score:
            sentiment = 'negative'
            confidence = (negative_score - positive_score) / total_words if total_words > 0 else 0
        else:
            sentiment = 'neutral'
            confidence = neutral_score / total_words if total_words > 0 else 0
        
        return {
            'sentiment': sentiment,
            'confidence': min(confidence, 1.0),
            'scores': {
                'positive': positive_score,
                'negative': negative_score,
                'neutral': neutral_score
            },
            'total_words': total_words
        }
    
    def process(self, input_data: Any) -> Any:
        """
        Analyze sentiment of input text
        Args:
            input_data: Text string or file path containing text
        Returns:
            Sentiment analysis result
        """
        try:
            # Handle different input types
            if isinstance(input_data, str):
                if os.path.isfile(input_data):
                    # Read from file
                    with open(input_data, 'r', encoding='utf-8') as f:
                        text = f.read()
                    source = f"file: {input_data}"
                else:
                    # Direct text input
                    text = input_data
                    source = "direct input"
            else:
                return {"error": "Input must be a string (text or file path)"}
            
            if not text.strip():
                return {"error": "Empty text provided"}
            
            # Preprocess text
            words = self._preprocess_text(text)
            
            # Calculate sentiment
            sentiment_result = self._calculate_sentiment(words)
            
            # Find sentiment words used
            positive_found = [word for word in words if word in self.positive_words]
            negative_found = [word for word in words if word in self.negative_words]
            
            return {
                'text_preview': text[:100] + ('...' if len(text) > 100 else ''),
                'source': source,
                'sentiment': sentiment_result['sentiment'],
                'confidence': round(sentiment_result['confidence'], 2),
                'scores': sentiment_result['scores'],
                'total_words': sentiment_result['total_words'],
                'sentiment_words': {
                    'positive_found': positive_found,
                    'negative_found': negative_found
                }
            }
            
        except Exception as e:
            return {"error": f"Sentiment analysis failed: {str(e)}"}
    
    def get_requirements(self) -> List[str]:
        """Return required packages"""
        return []  # No external packages needed for basic implementation
    
    def get_description(self) -> str:
        """Task description"""
        return "Analyze sentiment of text using word-based approach"

# Test function
if __name__ == "__main__":
    task = TextSentimentTask()
    
    # Test with sample texts
    test_texts = [
        "I love this product! It's amazing and works perfectly.",
        "This is terrible. I hate it and it's completely useless.",
        "The weather is okay today. Nothing special."
    ]
    
    for text in test_texts:
        result = task.process(text)
        print(f"Text: {text}")
        print(f"Result: {result}")
        print("-" * 50)