import asyncio
from typing import List, Dict, Any, Optional
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import time

class WebSearchService:
    """Service for searching the web for current movie industry information."""
    
    def __init__(self):
        self.ddgs = DDGS()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    async def search_movie_industry(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Search for movie industry information online.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with content and metadata
        """
        try:
            # Add movie industry context to the query
            enhanced_query = f"movie industry {query}"
            
            # Search using DuckDuckGo (free, no API key required)
            search_results = []
            for result in self.ddgs.text(enhanced_query, max_results=max_results):
                search_results.append({
                    'title': result.get('title', ''),
                    'url': result.get('link', ''),
                    'snippet': result.get('body', ''),
                    'source_type': 'web_search'
                })
            
            # Enhance results with content extraction
            enhanced_results = []
            for result in search_results:
                try:
                    # Extract more content from the webpage
                    content = await self._extract_webpage_content(result['url'])
                    if content:
                        result['content'] = content
                        result['word_count'] = len(content.split())
                        enhanced_results.append(result)
                except Exception as e:
                    print(f"Error extracting content from {result['url']}: {e}")
                    # Still include the result with just the snippet
                    result['content'] = result['snippet']
                    result['word_count'] = len(result['snippet'].split())
                    enhanced_results.append(result)
                
                # Rate limiting to be respectful
                await asyncio.sleep(1)
            
            return enhanced_results[:max_results]
            
        except Exception as e:
            print(f"Error in web search: {e}")
            return []
    
    async def _extract_webpage_content(self, url: str) -> Optional[str]:
        """
        Extract readable content from a webpage.
        
        Args:
            url: URL to extract content from
            
        Returns:
            Extracted text content or None if failed
        """
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return None
            
            # Fetch webpage content
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()
            
            # Extract text content
            text_content = soup.get_text()
            
            # Clean up the text
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit content length to avoid overwhelming the LLM
            if len(text) > 2000:
                text = text[:2000] + "..."
            
            return text
            
        except Exception as e:
            print(f"Error extracting content from {url}: {e}")
            return None
    
    def validate_web_source(self, url: str) -> Dict[str, Any]:
        """
        Validate a web source for credibility.
        
        Args:
            url: URL to validate
            
        Returns:
            Validation result with credibility score and warnings
        """
        validation = {
            'is_valid': True,
            'credibility_score': 0.5,  # Default neutral score
            'warnings': [],
            'domain_authority': 'unknown'
        }
        
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Check for known movie industry domains
            industry_domains = [
                'imdb.com', 'variety.com', 'hollywoodreporter.com', 'deadline.com',
                'thewrap.com', 'indiewire.com', 'screenrant.com', 'collider.com',
                'movieinsider.com', 'filmmaker.com', 'cinematography.com'
            ]
            
            if any(ind_domain in domain for ind_domain in industry_domains):
                validation['credibility_score'] = 0.8
                validation['domain_authority'] = 'industry_recognized'
            elif 'wikipedia.org' in domain:
                validation['credibility_score'] = 0.7
                validation['domain_authority'] = 'wikipedia'
            elif domain.endswith('.edu'):
                validation['credibility_score'] = 0.9
                validation['domain_authority'] = 'educational'
            elif domain.endswith('.gov'):
                validation['credibility_score'] = 0.9
                validation['domain_authority'] = 'government'
            
            # Check for suspicious patterns
            suspicious_patterns = [
                r'\.blogspot\.', r'\.wordpress\.', r'\.tumblr\.',
                r'\.weebly\.', r'\.wixsite\.', r'\.000webhost\.'
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, domain):
                    validation['warnings'].append(f"Low-authority domain: {domain}")
                    validation['credibility_score'] *= 0.7
            
            # Final validation
            validation['is_valid'] = validation['credibility_score'] > 0.3
            
        except Exception as e:
            validation['is_valid'] = False
            validation['warnings'].append(f"Validation error: {str(e)}")
        
        return validation
    
    def format_web_source_citation(self, result: Dict[str, Any]) -> str:
        """
        Format a web source for citation in responses.
        
        Args:
            result: Web search result
            
        Returns:
            Formatted citation string
        """
        title = result.get('title', 'Unknown Title')
        url = result.get('url', '')
        domain = urlparse(url).netloc if url else 'Unknown Source'
        
        return f"[{title}]({url}) from {domain}"
