"""
Conversation Analyzer - Module for analyzing conversation context and patterns
Handles conversation analysis, context extraction, and pattern recognition
"""

import asyncio
import re
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import sqlite3
from collections import defaultdict, deque
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from textblob import TextBlob

logger = logging.getLogger(__name__)

class ConversationAnalyzer:
    def __init__(self):
        self.context_window = 10  # Number of messages to keep in context
        self.conversation_history = defaultdict(lambda: deque(maxlen=self.context_window))
        self.pattern_database = {}
        self.emotion_patterns = {
            'happy': ['😊', '😄', '😃', '😁', '😆', '😅', '😂', '🤣', '😋', '😎'],
            'sad': ['😢', '😭', '😔', '😞', '😟', '😕', '😣', '😖', '😫', '😩'],
            'angry': ['😠', '😡', '🤬', '😤', '😾', '💢', '😈', '👿'],
            'surprised': ['😲', '😳', '😱', '😨', '😰', '😯', '😦', '😧'],
            'love': ['😍', '🥰', '😘', '😗', '😙', '😚', '💕', '💖', '💗', '💘']
        }
        
        # Load NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
        
        self.stop_words = set(stopwords.words('english'))
        self.init_database()
    
    def init_database(self):
        """Initialize the conversation analysis database"""
        try:
            conn = sqlite3.connect('ranger_ai.db')
            cursor = conn.cursor()
            
            # Create conversation analysis table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT,
                    user_id TEXT,
                    message_content TEXT,
                    sentiment_score REAL,
                    emotion TEXT,
                    topics TEXT,
                    context_keywords TEXT,
                    timestamp TEXT,
                    message_length INTEGER,
                    word_count INTEGER,
                    has_question BOOLEAN,
                    has_command BOOLEAN,
                    has_mention BOOLEAN
                )
            ''')
            
            # Create conversation patterns table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT,
                    pattern_data TEXT,
                    frequency INTEGER DEFAULT 1,
                    first_seen TEXT,
                    last_seen TEXT,
                    confidence REAL DEFAULT 0.0
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conv_channel ON conversation_analysis (channel_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conv_user ON conversation_analysis (user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conv_timestamp ON conversation_analysis (timestamp)')
            
            conn.commit()
            conn.close()
            
            logger.info("Conversation analysis database initialized")
            
        except Exception as e:
            logger.error(f"Error initializing conversation analysis database: {e}")
    
    async def analyze_context(self, message) -> Dict[str, Any]:
        """Analyze the context of a message"""
        try:
            # Extract basic message info
            channel_id = str(message.channel.id)
            user_id = str(message.author.id)
            content = message.content
            timestamp = datetime.now().isoformat()
            
            # Analyze message content
            analysis = await self._analyze_message_content(content)
            
            # Get conversation history
            history = self.conversation_history[channel_id]
            
            # Add current message to history
            history.append({
                'user_id': user_id,
                'content': content,
                'timestamp': timestamp,
                'analysis': analysis
            })
            
            # Analyze conversation context
            context = await self._analyze_conversation_context(channel_id, history)
            
            # Store analysis in database
            await self._store_analysis(channel_id, user_id, content, analysis, timestamp)
            
            # Update patterns
            await self._update_patterns(analysis, context)
            
            return {
                'message_analysis': analysis,
                'conversation_context': context,
                'history_length': len(history),
                'channel_id': channel_id,
                'user_id': user_id
            }
            
        except Exception as e:
            logger.error(f"Error analyzing context: {e}")
            return {}
    
    async def _analyze_message_content(self, content: str) -> Dict[str, Any]:
        """Analyze the content of a single message"""
        try:
            # Basic text analysis
            word_count = len(content.split())
            message_length = len(content)
            
            # Sentiment analysis
            blob = TextBlob(content)
            sentiment_score = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            
            # Emotion detection
            emotion = self._detect_emotion(content)
            
            # Topic extraction
            topics = self._extract_topics(content)
            
            # Context keywords
            keywords = self._extract_keywords(content)
            
            # Question detection
            has_question = '?' in content or any(word in content.lower() for word in ['what', 'how', 'why', 'when', 'where', 'who'])
            
            # Command detection
            has_command = content.startswith('!') or any(word in content.lower() for word in ['please', 'can you', 'could you', 'would you'])
            
            # Mention detection
            has_mention = '<@' in content and '>' in content
            
            return {
                'word_count': word_count,
                'message_length': message_length,
                'sentiment_score': sentiment_score,
                'subjectivity': subjectivity,
                'emotion': emotion,
                'topics': topics,
                'keywords': keywords,
                'has_question': has_question,
                'has_command': has_command,
                'has_mention': has_mention,
                'complexity_score': self._calculate_complexity(content)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing message content: {e}")
            return {}
    
    def _detect_emotion(self, content: str) -> str:
        """Detect emotion from message content"""
        try:
            # Check for emojis
            for emotion, emojis in self.emotion_patterns.items():
                if any(emoji in content for emoji in emojis):
                    return emotion
            
            # Check for emotion words
            emotion_words = {
                'happy': ['happy', 'joy', 'excited', 'great', 'awesome', 'amazing'],
                'sad': ['sad', 'depressed', 'unhappy', 'terrible', 'awful', 'horrible'],
                'angry': ['angry', 'mad', 'furious', 'annoyed', 'irritated'],
                'surprised': ['surprised', 'shocked', 'amazed', 'wow', 'incredible'],
                'love': ['love', 'adore', 'like', 'heart', 'cute', 'sweet']
            }
            
            content_lower = content.lower()
            for emotion, words in emotion_words.items():
                if any(word in content_lower for word in words):
                    return emotion
            
            # Default to neutral
            return 'neutral'
            
        except Exception as e:
            logger.error(f"Error detecting emotion: {e}")
            return 'neutral'
    
    def _extract_topics(self, content: str) -> List[str]:
        """Extract topics from message content"""
        try:
            # Simple topic extraction based on keywords
            topics = []
            
            # Common topic keywords
            topic_keywords = {
                'technology': ['computer', 'programming', 'code', 'software', 'hardware', 'ai', 'machine learning'],
                'science': ['science', 'research', 'experiment', 'theory', 'discovery'],
                'politics': ['politics', 'government', 'election', 'policy', 'democracy'],
                'sports': ['sports', 'game', 'team', 'player', 'match', 'tournament'],
                'entertainment': ['movie', 'music', 'book', 'show', 'entertainment', 'celebrity'],
                'food': ['food', 'cooking', 'recipe', 'restaurant', 'meal', 'cuisine'],
                'travel': ['travel', 'vacation', 'trip', 'destination', 'hotel', 'flight']
            }
            
            content_lower = content.lower()
            for topic, keywords in topic_keywords.items():
                if any(keyword in content_lower for keyword in keywords):
                    topics.append(topic)
            
            return topics
            
        except Exception as e:
            logger.error(f"Error extracting topics: {e}")
            return []
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract important keywords from content"""
        try:
            # Tokenize and remove stop words
            words = word_tokenize(content.lower())
            words = [word for word in words if word.isalnum() and word not in self.stop_words]
            
            # Count word frequency
            word_freq = defaultdict(int)
            for word in words:
                word_freq[word] += 1
            
            # Return most frequent words (up to 5)
            keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            return [word for word, freq in keywords[:5]]
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []
    
    def _calculate_complexity(self, content: str) -> float:
        """Calculate text complexity score"""
        try:
            sentences = sent_tokenize(content)
            words = word_tokenize(content)
            
            if not sentences or not words:
                return 0.0
            
            # Average sentence length
            avg_sentence_length = len(words) / len(sentences)
            
            # Unique word ratio
            unique_ratio = len(set(words)) / len(words) if words else 0
            
            # Complexity score (0-1)
            complexity = min(1.0, (avg_sentence_length / 20) + (unique_ratio * 0.5))
            
            return complexity
            
        except Exception as e:
            logger.error(f"Error calculating complexity: {e}")
            return 0.0
    
    async def _analyze_conversation_context(self, channel_id: str, history: deque) -> Dict[str, Any]:
        """Analyze the broader conversation context"""
        try:
            if not history:
                return {}
            
            # Recent messages analysis
            recent_messages = list(history)[-5:]  # Last 5 messages
            
            # Overall sentiment trend
            sentiments = [msg['analysis'].get('sentiment_score', 0) for msg in recent_messages]
            sentiment_trend = sum(sentiments) / len(sentiments) if sentiments else 0
            
            # Conversation flow
            questions_count = sum(1 for msg in recent_messages if msg['analysis'].get('has_question', False))
            commands_count = sum(1 for msg in recent_messages if msg['analysis'].get('has_command', False))
            
            # Topic consistency
            all_topics = []
            for msg in recent_messages:
                all_topics.extend(msg['analysis'].get('topics', []))
            
            topic_frequency = defaultdict(int)
            for topic in all_topics:
                topic_frequency[topic] += 1
            
            dominant_topics = sorted(topic_frequency.items(), key=lambda x: x[1], reverse=True)[:3]
            
            # User engagement
            unique_users = len(set(msg['user_id'] for msg in recent_messages))
            engagement_score = unique_users / len(recent_messages) if recent_messages else 0
            
            return {
                'sentiment_trend': sentiment_trend,
                'questions_count': questions_count,
                'commands_count': commands_count,
                'dominant_topics': dict(dominant_topics),
                'engagement_score': engagement_score,
                'conversation_length': len(history),
                'recent_activity': len([msg for msg in recent_messages if msg['timestamp'] > (datetime.now() - timedelta(minutes=5)).isoformat()])
            }
            
        except Exception as e:
            logger.error(f"Error analyzing conversation context: {e}")
            return {}
    
    async def _store_analysis(self, channel_id: str, user_id: str, content: str, analysis: Dict[str, Any], timestamp: str):
        """Store conversation analysis in database"""
        try:
            conn = sqlite3.connect('ranger_ai.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO conversation_analysis 
                (channel_id, user_id, message_content, sentiment_score, emotion, topics, 
                 context_keywords, timestamp, message_length, word_count, has_question, 
                 has_command, has_mention)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                channel_id,
                user_id,
                content,
                analysis.get('sentiment_score', 0),
                analysis.get('emotion', 'neutral'),
                json.dumps(analysis.get('topics', [])),
                json.dumps(analysis.get('keywords', [])),
                timestamp,
                analysis.get('message_length', 0),
                analysis.get('word_count', 0),
                analysis.get('has_question', False),
                analysis.get('has_command', False),
                analysis.get('has_mention', False)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing analysis: {e}")
    
    async def _update_patterns(self, analysis: Dict[str, Any], context: Dict[str, Any]):
        """Update conversation patterns based on analysis"""
        try:
            # Create pattern key
            pattern_key = f"{analysis.get('emotion', 'neutral')}_{analysis.get('has_question', False)}_{analysis.get('has_command', False)}"
            
            # Update pattern frequency
            if pattern_key in self.pattern_database:
                self.pattern_database[pattern_key]['frequency'] += 1
                self.pattern_database[pattern_key]['last_seen'] = datetime.now().isoformat()
            else:
                self.pattern_database[pattern_key] = {
                    'frequency': 1,
                    'first_seen': datetime.now().isoformat(),
                    'last_seen': datetime.now().isoformat(),
                    'confidence': 0.0
                }
            
            # Update confidence based on frequency
            total_patterns = sum(pattern['frequency'] for pattern in self.pattern_database.values())
            if total_patterns > 0:
                self.pattern_database[pattern_key]['confidence'] = self.pattern_database[pattern_key]['frequency'] / total_patterns
            
        except Exception as e:
            logger.error(f"Error updating patterns: {e}")
    
    async def get_conversation_stats(self, channel_id: str = None, time_period: str = '24h') -> Dict[str, Any]:
        """Get conversation statistics"""
        try:
            conn = sqlite3.connect('ranger_ai.db')
            cursor = conn.cursor()
            
            # Calculate time filter
            if time_period == '24h':
                time_filter = (datetime.now() - timedelta(hours=24)).isoformat()
            elif time_period == '7d':
                time_filter = (datetime.now() - timedelta(days=7)).isoformat()
            else:
                time_filter = (datetime.now() - timedelta(hours=1)).isoformat()
            
            # Build query
            query = 'SELECT * FROM conversation_analysis WHERE timestamp > ?'
            params = [time_filter]
            
            if channel_id:
                query += ' AND channel_id = ?'
                params.append(channel_id)
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if not results:
                return {'total_messages': 0, 'avg_sentiment': 0, 'top_emotions': [], 'top_topics': []}
            
            # Calculate statistics
            total_messages = len(results)
            sentiments = [row[4] for row in results if row[4] is not None]
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
            
            # Top emotions
            emotions = [row[5] for row in results if row[5]]
            emotion_counts = defaultdict(int)
            for emotion in emotions:
                emotion_counts[emotion] += 1
            top_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Top topics
            all_topics = []
            for row in results:
                if row[6]:  # topics column
                    try:
                        topics = json.loads(row[6])
                        all_topics.extend(topics)
                    except:
                        pass
            
            topic_counts = defaultdict(int)
            for topic in all_topics:
                topic_counts[topic] += 1
            top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            conn.close()
            
            return {
                'total_messages': total_messages,
                'avg_sentiment': round(avg_sentiment, 3),
                'top_emotions': top_emotions,
                'top_topics': top_topics,
                'time_period': time_period
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation stats: {e}")
            return {}
    
    async def get_user_patterns(self, user_id: str) -> Dict[str, Any]:
        """Get conversation patterns for a specific user"""
        try:
            conn = sqlite3.connect('ranger_ai.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT emotion, sentiment_score, has_question, has_command, topics
                FROM conversation_analysis 
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 100
            ''', (user_id,))
            
            results = cursor.fetchall()
            
            if not results:
                return {'message_count': 0, 'preferred_emotions': [], 'avg_sentiment': 0}
            
            # Analyze user patterns
            emotions = [row[0] for row in results if row[0]]
            emotion_counts = defaultdict(int)
            for emotion in emotions:
                emotion_counts[emotion] += 1
            
            sentiments = [row[1] for row in results if row[1] is not None]
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
            
            questions_count = sum(1 for row in results if row[2])
            commands_count = sum(1 for row in results if row[3])
            
            # Preferred topics
            all_topics = []
            for row in results:
                if row[4]:  # topics column
                    try:
                        topics = json.loads(row[4])
                        all_topics.extend(topics)
                    except:
                        pass
            
            topic_counts = defaultdict(int)
            for topic in all_topics:
                topic_counts[topic] += 1
            preferred_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            conn.close()
            
            return {
                'message_count': len(results),
                'preferred_emotions': sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)[:3],
                'avg_sentiment': round(avg_sentiment, 3),
                'questions_ratio': questions_count / len(results),
                'commands_ratio': commands_count / len(results),
                'preferred_topics': preferred_topics
            }
            
        except Exception as e:
            logger.error(f"Error getting user patterns: {e}")
            return {} 