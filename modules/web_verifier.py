"""
Web Verifier - Module for searching and verifying information from the web
Handles web searches, content extraction, and information verification
"""

import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
import re
import json
import logging
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
import time
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

class WebVerifier:
    def __init__(self):
        self.session = None
        self.search_engines = [
            'https://www.google.com/search',
            'https://www.bing.com/search',
            'https://duckduckgo.com/html/'
        ]
        self.trusted_domains = [
            'wikipedia.org',
            'britannica.com',
            'nasa.gov',
            'nih.gov',
            'who.int',
            'cdc.gov',
            'edu',
            'gov'
        ]
        self.max_results = 5
        self.timeout = 10
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={'User-Agent': self.user_agents[0]}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def search_web(self, query: str) -> Optional[str]:
        """Search the web for information about a topic"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    headers={'User-Agent': self.user_agents[0]}
                )
            
            # Try multiple search engines
            for engine in self.search_engines:
                try:
                    results = await self._search_engine(engine, query)
                    if results:
                        # Extract and verify content
                        verified_content = await self._extract_and_verify_content(results)
                        if verified_content:
                            return verified_content
                except Exception as e:
                    logger.warning(f"Search engine {engine} failed: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching web: {e}")
            return None
    
    async def _search_engine(self, engine_url: str, query: str) -> List[Dict[str, str]]:
        """Search using a specific search engine"""
        try:
            params = {
                'q': query,
                'num': self.max_results
            }
            
            async with self.session.get(engine_url, params=params) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_search_results(html, engine_url)
                else:
                    logger.warning(f"Search engine returned status {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error with search engine {engine_url}: {e}")
            return []
    
    def _parse_search_results(self, html: str, engine_url: str) -> List[Dict[str, str]]:
        """Parse search results from HTML"""
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Google-style results
        if 'google.com' in engine_url:
            for result in soup.find_all('div', class_='g'):
                title_elem = result.find('h3')
                link_elem = result.find('a')
                snippet_elem = result.find('div', class_='VwiC3b')
                
                if title_elem and link_elem:
                    results.append({
                        'title': title_elem.get_text(),
                        'url': link_elem.get('href', ''),
                        'snippet': snippet_elem.get_text() if snippet_elem else ''
                    })
        
        # Bing-style results
        elif 'bing.com' in engine_url:
            for result in soup.find_all('li', class_='b_algo'):
                title_elem = result.find('h2')
                link_elem = result.find('a')
                snippet_elem = result.find('p')
                
                if title_elem and link_elem:
                    results.append({
                        'title': title_elem.get_text(),
                        'url': link_elem.get('href', ''),
                        'snippet': snippet_elem.get_text() if snippet_elem else ''
                    })
        
        # DuckDuckGo-style results
        elif 'duckduckgo.com' in engine_url:
            for result in soup.find_all('div', class_='result'):
                title_elem = result.find('a', class_='result__a')
                snippet_elem = result.find('div', class_='result__snippet')
                
                if title_elem:
                    results.append({
                        'title': title_elem.get_text(),
                        'url': title_elem.get('href', ''),
                        'snippet': snippet_elem.get_text() if snippet_elem else ''
                    })
        
        return results[:self.max_results]
    
    async def _extract_and_verify_content(self, search_results: List[Dict[str, str]]) -> Optional[str]:
        """Extract content from search results and verify it"""
        verified_contents = []
        
        for result in search_results:
            try:
                # Check if domain is trusted
                domain = urlparse(result['url']).netloc
                trust_score = self._calculate_trust_score(domain)
                
                if trust_score > 0.5:  # Only process trusted sources
                    content = await self._extract_page_content(result['url'])
                    if content:
                        verified_contents.append({
                            'content': content,
                            'url': result['url'],
                            'trust_score': trust_score
                        })
                
            except Exception as e:
                logger.warning(f"Error extracting content from {result['url']}: {e}")
                continue
        
        if verified_contents:
            # Return the most trusted content
            best_content = max(verified_contents, key=lambda x: x['trust_score'])
            return best_content['content']
        
        return None
    
    def _calculate_trust_score(self, domain: str) -> float:
        """Calculate trust score for a domain"""
        score = 0.0
        
        # Check against trusted domains
        for trusted in self.trusted_domains:
            if trusted in domain:
                score += 0.8
                break
        
        # Additional scoring based on domain characteristics
        if domain.endswith('.edu'):
            score += 0.2
        elif domain.endswith('.gov'):
            score += 0.2
        elif domain.endswith('.org'):
            score += 0.1
        
        # Penalize suspicious domains
        suspicious_keywords = ['click', 'ad', 'spam', 'fake']
        for keyword in suspicious_keywords:
            if keyword in domain.lower():
                score -= 0.3
        
        return max(0.0, min(1.0, score))
    
    async def _extract_page_content(self, url: str) -> Optional[str]:
        """Extract main content from a webpage"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_page_content(html)
                else:
                    return None
                    
        except Exception as e:
            logger.warning(f"Error extracting content from {url}: {e}")
            return None
    
    def _parse_page_content(self, html: str) -> str:
        """Parse main content from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Try to find main content
        main_content = None
        
        # Look for common content containers
        content_selectors = [
            'main',
            'article',
            '.content',
            '.main-content',
            '#content',
            '#main',
            '.post-content',
            '.entry-content'
        ]
        
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            # Fallback to body
            main_content = soup.find('body')
        
        if main_content:
            # Extract text and clean it
            text = main_content.get_text()
            text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
            text = re.sub(r'[^\w\s\.\,\!\?\-]', '', text)  # Remove special chars
            
            # Limit length
            if len(text) > 2000:
                text = text[:2000] + "..."
            
            return text.strip()
        
        return ""
    
    async def verify_knowledge(self, knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Verify knowledge against web sources"""
        try:
            topic = knowledge.get('topic', '')
            content = knowledge.get('content', '')
            
            if not topic or not content:
                return {'is_verified': False, 'confidence': 0.0, 'sources': []}
            
            # Search for verification
            search_query = f"{topic} {content[:100]}"
            web_content = await self.search_web(search_query)
            
            if web_content:
                # Compare content similarity
                similarity = self._calculate_similarity(content, web_content)
                
                verification_result = {
                    'is_verified': similarity > 0.7,
                    'confidence': similarity,
                    'sources': [web_content[:200] + "..."] if similarity > 0.5 else [],
                    'verification_method': 'web_search',
                    'timestamp': datetime.now().isoformat()
                }
                
                return verification_result
            else:
                return {
                    'is_verified': False,
                    'confidence': 0.0,
                    'sources': [],
                    'verification_method': 'web_search',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error verifying knowledge: {e}")
            return {
                'is_verified': False,
                'confidence': 0.0,
                'sources': [],
                'error': str(e)
            }
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        try:
            # Simple word overlap similarity
            words1 = set(re.findall(r'\w+', text1.lower()))
            words2 = set(re.findall(r'\w+', text2.lower()))
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union) if union else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    async def get_verification_stats(self) -> Dict[str, Any]:
        """Get verification statistics"""
        try:
            # This would typically query a database
            # For now, return basic stats
            return {
                'total_verifications': 0,
                'successful_verifications': 0,
                'average_confidence': 0.0,
                'trusted_sources_used': 0
            }
            
        except Exception as e:
            logger.error(f"Error getting verification stats: {e}")
            return {}
    
    def update_trusted_domains(self, domains: List[str]):
        """Update the list of trusted domains"""
        self.trusted_domains.extend(domains)
        self.trusted_domains = list(set(self.trusted_domains))  # Remove duplicates
        logger.info(f"Updated trusted domains: {self.trusted_domains}")
    
    def update_timeout(self, timeout: int):
        """Update the request timeout"""
        self.timeout = timeout
        logger.info(f"Updated timeout to: {timeout} seconds") 