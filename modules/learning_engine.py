"""
Learning Engine - Core learning and knowledge extraction module
Handles learning from conversations, web content, and user interactions
"""

import asyncio
import re
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import sqlite3
from textblob import TextBlob
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

logger = logging.getLogger(__name__)

class LearningEngine:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.knowledge_patterns = [
            r'(?:did you know|fun fact|interesting|learned that)\s+(.+)',
            r'(?:the\s+)?(.+?)\s+(?:is|are|was|were)\s+(.+)',
            r'(?:I\s+)?(?:think|believe|know)\s+(?:that\s+)?(.+)',
            r'(?:according\s+to|sources\s+say|research\s+shows)\s+(.+)',
            r'(?:fact|truth|reality)\s+(?:is|about)\s+(.+)'
        ]
        self.learning_rate = 0.1
        self.min_confidence = 0.6
        
    async def extract_knowledge(self, text: str, context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Extract potential knowledge from text"""
        try:
            # Clean and preprocess text
            cleaned_text = self._preprocess_text(text)
            
            # Extract knowledge using patterns
            knowledge = self._extract_using_patterns(cleaned_text)
            
            if not knowledge:
                # Try semantic extraction
                knowledge = self._extract_semantic_knowledge(cleaned_text)
            
            if knowledge:
                # Add metadata
                knowledge['timestamp'] = datetime.now().isoformat()
                knowledge['source'] = 'conversation'
                knowledge['context'] = context or {}
                knowledge['confidence'] = self._calculate_confidence(knowledge)
                
                # Only return if confidence is high enough
                if knowledge['confidence'] >= self.min_confidence:
                    return knowledge
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting knowledge: {e}")
            return None
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for knowledge extraction"""
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove mentions and emojis
        text = re.sub(r'<@!?\d+>', '', text)
        text = re.sub(r'[^\w\s\.\,\!\?]', '', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _extract_using_patterns(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract knowledge using predefined patterns"""
        for pattern in self.knowledge_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Find the most complete match
                best_match = max(matches, key=len)
                if len(best_match) > 10:  # Minimum meaningful length
                    return {
                        'topic': self._extract_topic(best_match),
                        'content': best_match,
                        'extraction_method': 'pattern_matching'
                    }
        return None
    
    def _extract_semantic_knowledge(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract knowledge using semantic analysis"""
        try:
            # Tokenize and analyze
            sentences = sent_tokenize(text)
            
            for sentence in sentences:
                if len(sentence) < 20:  # Skip very short sentences
                    continue
                
                # Analyze sentiment and subjectivity
                blob = TextBlob(sentence)
                
                # Look for factual statements (low subjectivity, neutral sentiment)
                if blob.sentiment.subjectivity < 0.3 and abs(blob.sentiment.polarity) < 0.3:
                    # Extract potential facts
                    words = word_tokenize(sentence.lower())
                    words = [self.lemmatizer.lemmatize(word) for word in words if word not in self.stop_words]
                    
                    if len(words) > 5:  # Ensure sufficient content
                        return {
                            'topic': self._extract_topic(sentence),
                            'content': sentence,
                            'extraction_method': 'semantic_analysis',
                            'sentiment': {
                                'polarity': blob.sentiment.polarity,
                                'subjectivity': blob.sentiment.subjectivity
                            }
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in semantic knowledge extraction: {e}")
            return None
    
    def _extract_topic(self, text: str) -> str:
        """Extract the main topic from text"""
        try:
            # Use NLTK for topic extraction
            words = word_tokenize(text.lower())
            words = [word for word in words if word not in self.stop_words and len(word) > 2]
            
            # Find the most common noun/verb
            pos_tags = nltk.pos_tag(words)
            nouns = [word for word, pos in pos_tags if pos.startswith('NN')]
            verbs = [word for word, pos in pos_tags if pos.startswith('VB')]
            
            if nouns:
                return nouns[0]
            elif verbs:
                return verbs[0]
            else:
                return words[0] if words else "unknown"
                
        except Exception as e:
            logger.error(f"Error extracting topic: {e}")
            return "unknown"
    
    def _calculate_confidence(self, knowledge: Dict[str, Any]) -> float:
        """Calculate confidence score for extracted knowledge"""
        confidence = 0.5  # Base confidence
        
        # Factor in extraction method
        if knowledge.get('extraction_method') == 'pattern_matching':
            confidence += 0.2
        elif knowledge.get('extraction_method') == 'semantic_analysis':
            confidence += 0.1
        
        # Factor in content length
        content_length = len(knowledge.get('content', ''))
        if content_length > 50:
            confidence += 0.1
        elif content_length > 20:
            confidence += 0.05
        
        # Factor in sentiment (for semantic extraction)
        if 'sentiment' in knowledge:
            sentiment = knowledge['sentiment']
            if sentiment['subjectivity'] < 0.2:
                confidence += 0.1
            if abs(sentiment['polarity']) < 0.2:
                confidence += 0.1
        
        # Factor in context
        if knowledge.get('context'):
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    async def learn_from_unknown_command(self, command: str):
        """Learn from unknown commands to improve future responses"""
        try:
            # Store unknown command for analysis
            unknown_command = {
                'command': command,
                'timestamp': datetime.now().isoformat(),
                'type': 'unknown_command'
            }
            
            # Store in learning database
            await self._store_learning_data(unknown_command)
            
            logger.info(f"Learned from unknown command: {command}")
            
        except Exception as e:
            logger.error(f"Error learning from unknown command: {e}")
    
    async def learn_from_feedback(self, feedback: Dict[str, Any]):
        """Learn from user feedback"""
        try:
            feedback_data = {
                'feedback': feedback,
                'timestamp': datetime.now().isoformat(),
                'type': 'user_feedback'
            }
            
            await self._store_learning_data(feedback_data)
            
            logger.info(f"Learned from feedback: {feedback}")
            
        except Exception as e:
            logger.error(f"Error learning from feedback: {e}")
    
    async def _store_learning_data(self, data: Dict[str, Any]):
        """Store learning data in database"""
        try:
            conn = sqlite3.connect('ranger_ai.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_data
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 data TEXT,
                 timestamp TEXT,
                 type TEXT)
            ''')
            
            cursor.execute(
                'INSERT INTO learning_data (data, timestamp, type) VALUES (?, ?, ?)',
                (json.dumps(data), data['timestamp'], data['type'])
            )
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing learning data: {e}")
    
    async def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics"""
        try:
            conn = sqlite3.connect('ranger_ai.db')
            cursor = conn.cursor()
            
            # Get total learning data
            cursor.execute('SELECT COUNT(*) FROM learning_data')
            total_data = cursor.fetchone()[0]
            
            # Get data by type
            cursor.execute('SELECT type, COUNT(*) FROM learning_data GROUP BY type')
            type_counts = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'total_learning_data': total_data,
                'by_type': type_counts
            }
            
        except Exception as e:
            logger.error(f"Error getting learning stats: {e}")
            return {'total_learning_data': 0, 'by_type': {}}
    
    def update_learning_rate(self, new_rate: float):
        """Update the learning rate"""
        self.learning_rate = max(0.0, min(1.0, new_rate))
        logger.info(f"Updated learning rate to: {self.learning_rate}")
    
    def update_confidence_threshold(self, new_threshold: float):
        """Update the minimum confidence threshold"""
        self.min_confidence = max(0.0, min(1.0, new_threshold))
        logger.info(f"Updated confidence threshold to: {self.min_confidence}") 