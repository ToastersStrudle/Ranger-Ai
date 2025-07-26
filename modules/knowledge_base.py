"""
Knowledge Base - Module for storing and managing learned information
Handles knowledge storage, retrieval, and consolidation
"""

import asyncio
import sqlite3
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib
import pickle
from pathlib import Path

logger = logging.getLogger(__name__)

class KnowledgeBase:
    def __init__(self):
        self.db_path = 'ranger_ai.db'
        self.knowledge_table = 'knowledge'
        self.verification_table = 'verifications'
        self.consolidation_table = 'consolidations'
        self.init_database()
    
    def init_database(self):
        """Initialize the knowledge base database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create knowledge table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT,
                    extraction_method TEXT,
                    confidence REAL DEFAULT 0.0,
                    verified BOOLEAN DEFAULT FALSE,
                    verification_confidence REAL DEFAULT 0.0,
                    timestamp TEXT,
                    last_accessed TEXT,
                    access_count INTEGER DEFAULT 0,
                    tags TEXT,
                    metadata TEXT
                )
            ''')
            
            # Create verifications table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS verifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    knowledge_id INTEGER,
                    verification_method TEXT,
                    is_verified BOOLEAN,
                    confidence REAL,
                    sources TEXT,
                    timestamp TEXT,
                    FOREIGN KEY (knowledge_id) REFERENCES knowledge (id)
                )
            ''')
            
            # Create consolidations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS consolidations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_ids TEXT,
                    consolidated_content TEXT,
                    consolidation_method TEXT,
                    timestamp TEXT
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_topic ON knowledge (topic)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_verified ON knowledge (verified)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_confidence ON knowledge (confidence)')
            
            conn.commit()
            conn.close()
            
            logger.info("Knowledge base database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing knowledge base: {e}")
    
    async def store_knowledge(self, knowledge: Dict[str, Any], verification_result: Dict[str, Any] = None):
        """Store new knowledge in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Prepare knowledge data
            knowledge_data = {
                'topic': knowledge.get('topic', 'unknown'),
                'content': knowledge.get('content', ''),
                'source': knowledge.get('source', 'conversation'),
                'extraction_method': knowledge.get('extraction_method', 'unknown'),
                'confidence': knowledge.get('confidence', 0.0),
                'verified': verification_result.get('is_verified', False) if verification_result else False,
                'verification_confidence': verification_result.get('confidence', 0.0) if verification_result else 0.0,
                'timestamp': datetime.now().isoformat(),
                'last_accessed': datetime.now().isoformat(),
                'access_count': 0,
                'tags': json.dumps(knowledge.get('tags', [])),
                'metadata': json.dumps(knowledge.get('metadata', {}))
            }
            
            # Insert knowledge
            cursor.execute('''
                INSERT INTO knowledge 
                (topic, content, source, extraction_method, confidence, verified, 
                 verification_confidence, timestamp, last_accessed, access_count, tags, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                knowledge_data['topic'],
                knowledge_data['content'],
                knowledge_data['source'],
                knowledge_data['extraction_method'],
                knowledge_data['confidence'],
                knowledge_data['verified'],
                knowledge_data['verification_confidence'],
                knowledge_data['timestamp'],
                knowledge_data['last_accessed'],
                knowledge_data['access_count'],
                knowledge_data['tags'],
                knowledge_data['metadata']
            ))
            
            knowledge_id = cursor.lastrowid
            
            # Store verification result if provided
            if verification_result:
                cursor.execute('''
                    INSERT INTO verifications 
                    (knowledge_id, verification_method, is_verified, confidence, sources, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    knowledge_id,
                    verification_result.get('verification_method', 'unknown'),
                    verification_result.get('is_verified', False),
                    verification_result.get('confidence', 0.0),
                    json.dumps(verification_result.get('sources', [])),
                    datetime.now().isoformat()
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Stored knowledge: {knowledge_data['topic']}")
            return knowledge_id
            
        except Exception as e:
            logger.error(f"Error storing knowledge: {e}")
            return None
    
    async def search_knowledge(self, query: str, limit: int = 5) -> Optional[Dict[str, Any]]:
        """Search for knowledge in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Search by topic or content
            cursor.execute('''
                SELECT id, topic, content, source, confidence, verified, 
                       verification_confidence, access_count, tags, metadata
                FROM knowledge 
                WHERE topic LIKE ? OR content LIKE ?
                ORDER BY confidence DESC, verified DESC, access_count DESC
                LIMIT ?
            ''', (f'%{query}%', f'%{query}%', limit))
            
            results = cursor.fetchall()
            
            if results:
                # Get the best match
                best_result = results[0]
                
                # Update access count and last accessed
                cursor.execute('''
                    UPDATE knowledge 
                    SET access_count = access_count + 1, last_accessed = ?
                    WHERE id = ?
                ''', (datetime.now().isoformat(), best_result[0]))
                
                conn.commit()
                
                knowledge = {
                    'id': best_result[0],
                    'topic': best_result[1],
                    'content': best_result[2],
                    'source': best_result[3],
                    'confidence': best_result[4],
                    'verified': bool(best_result[5]),
                    'verification_confidence': best_result[6],
                    'access_count': best_result[7],
                    'tags': json.loads(best_result[8]) if best_result[8] else [],
                    'metadata': json.loads(best_result[9]) if best_result[9] else {}
                }
                
                conn.close()
                return knowledge
            
            conn.close()
            return None
            
        except Exception as e:
            logger.error(f"Error searching knowledge: {e}")
            return None
    
    async def get_knowledge_count(self) -> int:
        """Get total number of knowledge items"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM knowledge')
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
            
        except Exception as e:
            logger.error(f"Error getting knowledge count: {e}")
            return 0
    
    async def get_verified_knowledge_count(self) -> int:
        """Get number of verified knowledge items"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM knowledge WHERE verified = TRUE')
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
            
        except Exception as e:
            logger.error(f"Error getting verified knowledge count: {e}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get total count
            cursor.execute('SELECT COUNT(*) FROM knowledge')
            total = cursor.fetchone()[0]
            
            # Get verified count
            cursor.execute('SELECT COUNT(*) FROM knowledge WHERE verified = TRUE')
            verified = cursor.fetchone()[0]
            
            # Get uncertain count (low confidence)
            cursor.execute('SELECT COUNT(*) FROM knowledge WHERE confidence < 0.5')
            uncertain = cursor.fetchone()[0]
            
            # Get average confidence
            cursor.execute('SELECT AVG(confidence) FROM knowledge')
            avg_confidence = cursor.fetchone()[0] or 0.0
            
            # Get most accessed topics
            cursor.execute('''
                SELECT topic, SUM(access_count) as total_access
                FROM knowledge 
                GROUP BY topic 
                ORDER BY total_access DESC 
                LIMIT 5
            ''')
            top_topics = cursor.fetchall()
            
            conn.close()
            
            return {
                'total': total,
                'verified': verified,
                'uncertain': uncertain,
                'average_confidence': round(avg_confidence, 3),
                'top_topics': [{'topic': topic, 'accesses': accesses} for topic, accesses in top_topics]
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'total': 0, 'verified': 0, 'uncertain': 0, 'average_confidence': 0.0, 'top_topics': []}
    
    async def consolidate_knowledge(self):
        """Consolidate similar knowledge items"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find similar knowledge items
            cursor.execute('''
                SELECT id, topic, content, confidence, verified
                FROM knowledge 
                WHERE verified = TRUE
                ORDER BY topic, confidence DESC
            ''')
            
            knowledge_items = cursor.fetchall()
            
            consolidated_count = 0
            
            # Group by topic and consolidate
            current_topic = None
            similar_items = []
            
            for item in knowledge_items:
                item_id, topic, content, confidence, verified = item
                
                if topic != current_topic:
                    # Process previous group
                    if len(similar_items) > 1:
                        consolidated = await self._consolidate_similar_items(similar_items)
                        if consolidated:
                            consolidated_count += 1
                    
                    # Start new group
                    current_topic = topic
                    similar_items = [item]
                else:
                    similar_items.append(item)
            
            # Process last group
            if len(similar_items) > 1:
                consolidated = await self._consolidate_similar_items(similar_items)
                if consolidated:
                    consolidated_count += 1
            
            conn.close()
            
            if consolidated_count > 0:
                logger.info(f"Consolidated {consolidated_count} knowledge groups")
            
        except Exception as e:
            logger.error(f"Error consolidating knowledge: {e}")
    
    async def _consolidate_similar_items(self, items: List[tuple]) -> bool:
        """Consolidate similar knowledge items"""
        try:
            # Find the best item (highest confidence and verified)
            best_item = max(items, key=lambda x: (x[4], x[3]))  # (verified, confidence)
            
            # Create consolidated content
            consolidated_content = best_item[2]  # Start with best content
            
            # Add additional information from other items
            additional_info = []
            for item in items:
                if item[0] != best_item[0]:  # Skip the best item
                    content = item[2]
                    if len(content) > 20 and content not in consolidated_content:
                        additional_info.append(content)
            
            if additional_info:
                consolidated_content += "\n\nAdditional information:\n" + "\n".join(additional_info[:3])
            
            # Store consolidation record
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            original_ids = [str(item[0]) for item in items]
            
            cursor.execute('''
                INSERT INTO consolidations 
                (original_ids, consolidated_content, consolidation_method, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (
                json.dumps(original_ids),
                consolidated_content,
                'similarity_merge',
                datetime.now().isoformat()
            ))
            
            # Update the best item with consolidated content
            cursor.execute('''
                UPDATE knowledge 
                SET content = ?, confidence = ?
                WHERE id = ?
            ''', (consolidated_content, best_item[3] + 0.1, best_item[0]))
            
            # Mark other items as consolidated
            for item in items:
                if item[0] != best_item[0]:
                    cursor.execute('''
                        UPDATE knowledge 
                        SET content = ?, verified = FALSE
                        WHERE id = ?
                    ''', (f"[Consolidated into item {best_item[0]}]", item[0]))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error consolidating similar items: {e}")
            return False
    
    async def backup_knowledge(self, backup_path: str = None):
        """Create a backup of the knowledge base"""
        try:
            if not backup_path:
                backup_path = f"knowledge_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            logger.info(f"Knowledge base backed up to: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Error backing up knowledge base: {e}")
            return None
    
    async def restore_knowledge(self, backup_path: str):
        """Restore knowledge base from backup"""
        try:
            import shutil
            shutil.copy2(backup_path, self.db_path)
            
            logger.info(f"Knowledge base restored from: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring knowledge base: {e}")
            return False
    
    async def export_knowledge(self, export_path: str = None):
        """Export knowledge to JSON format"""
        try:
            if not export_path:
                export_path = f"knowledge_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT topic, content, source, confidence, verified, 
                       verification_confidence, timestamp, tags, metadata
                FROM knowledge
                ORDER BY timestamp DESC
            ''')
            
            knowledge_items = cursor.fetchall()
            
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'total_items': len(knowledge_items),
                'knowledge': []
            }
            
            for item in knowledge_items:
                knowledge_item = {
                    'topic': item[0],
                    'content': item[1],
                    'source': item[2],
                    'confidence': item[3],
                    'verified': bool(item[4]),
                    'verification_confidence': item[5],
                    'timestamp': item[6],
                    'tags': json.loads(item[7]) if item[7] else [],
                    'metadata': json.loads(item[8]) if item[8] else {}
                }
                export_data['knowledge'].append(knowledge_item)
            
            conn.close()
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Knowledge exported to: {export_path}")
            return export_path
            
        except Exception as e:
            logger.error(f"Error exporting knowledge: {e}")
            return None 