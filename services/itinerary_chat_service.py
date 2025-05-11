"""
Itinerary Chat Service - Handles Q&A about the generated itinerary using Google's Gemini API.
"""

import os
import re
import logging
import requests
import json
import time
import random
import ssl
from typing import Dict, List, Any, Optional, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import google.generativeai as genai
from urllib.robotparser import RobotFileParser

logger = logging.getLogger(__name__)

class ItineraryChatService:
    """Service for answering questions about the itinerary using Gemini API"""
    
    # Common problematic URL patterns to avoid
    PROBLEMATIC_DOMAINS = [
        'facebook.com', 'instagram.com', 'twitter.com', 'linkedin.com',
        'booking.com', 'expedia.com', 'airbnb.com'  # Often block scrapers
    ]
    
    # Widely used user agent strings
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/112.0",
        "Mozilla/5.0 (iPad; CPU OS 16_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/112.0.5615.70 Mobile/15E148 Safari/604.1"
    ]
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the chat service with the Gemini API"""
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
        self.model = None
        self.itinerary_text = None
        self.destination = ""
        self.url_contents = ""
        self.chat_history = []
        self.robots_cache = {}  # Cache for robots.txt parsers
        
    def initialize_chain(self, narrative: Dict[str, Any]) -> None:
        """Initialize the model and context with the itinerary data"""
        if not self.api_key:
            logger.warning("Gemini API key not found. Chat functionality is disabled.")
            return
            
        try:
            # Try to extract destination from narrative
            main_text = narrative.get("main_narrative", "")
            first_line = main_text.split("\n")[0] if main_text else ""
            destination_match = re.search(r'in ([A-Za-z\s,]+)', first_line)
            self.destination = destination_match.group(1) if destination_match else ""
            
            # Extract all text content from the narrative
            daily_plans = "\n\n".join([f"Day {p['day']}: {p['content']}" for p in narrative.get("daily_plans", [])])
            budget_text = narrative.get("budget_narrative", "")
            
            # Combine into a single document
            self.itinerary_text = f"TRAVEL ITINERARY\n\n{main_text}\n\nDAILY PLANS:\n{daily_plans}\n\nBUDGET:\n{budget_text}"
            
            # Extract URLs from markdown links [text](url)
            urls = self._extract_urls_from_markdown(self.itinerary_text)
            filtered_urls = self._filter_problematic_urls(urls)
            
            # Scrape content from the URLs (with rate limiting and respect for robots.txt)
            self.url_contents = self._scrape_url_contents(filtered_urls)
            
            # Initialize Gemini model
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            
            # Reset chat history
            self.chat_history = []
            
            logger.info("Gemini chat service initialized successfully with itinerary data")
            
        except Exception as e:
            logger.error(f"Error initializing Gemini chat service: {e}")
            self.model = None

    
    def _extract_urls_from_markdown(self, text: str) -> List[str]:
        """Extract URLs from markdown links [text](url)"""
        url_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        matches = re.findall(url_pattern, text)
        return [url for _, url in matches if not url.startswith("https://www.google.com/search")]
    
    def _filter_problematic_urls(self, urls: List[str]) -> List[str]:
        """Filter out URLs that are known to be problematic for scraping"""
        filtered = []
        for url in urls:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Skip if domain contains problematic patterns
            if any(pd in domain for pd in self.PROBLEMATIC_DOMAINS):
                logger.info(f"Skipping problematic domain: {domain}")
                continue
                
            filtered.append(url)
        return filtered
    
    def _check_robots_txt(self, url: str) -> bool:
        """Check if scraping is allowed by robots.txt"""
        try:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            # Check cache first
            if base_url in self.robots_cache:
                rp = self.robots_cache[base_url]
            else:
                # Create and cache new parser
                rp = RobotFileParser()
                rp.set_url(f"{base_url}/robots.txt")
                try:
                    rp.read()
                    self.robots_cache[base_url] = rp
                except Exception as e:
                    logger.warning(f"Error reading robots.txt for {base_url}: {e}")
                    return True  # Allow by default if can't read robots.txt
            
            # Check if user-agent is allowed to fetch the URL
            path = parsed.path or "/"
            return rp.can_fetch("*", f"{base_url}{path}")
            
        except Exception as e:
            logger.warning(f"Error checking robots.txt: {e}")
            return True  # Allow by default in case of error
    
    def _get_ssl_context(self) -> ssl.SSLContext:
        """Create a more permissive SSL context for older websites"""
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context
    
    def _scrape_url_contents(self, urls: List[str], max_urls: int = 8) -> str:
        """Scrape content from URLs with improved error handling and retries"""
        all_content = []
        
        # Limit the number of URLs to scrape
        urls = urls[:max_urls]
        
        for url in urls:
            # Apply rate limiting
            time.sleep(random.uniform(1.0, 2.5))  # Random delay between requests
            
            try:
                # Check if this is a valid URL
                parsed = urlparse(url)
                if not parsed.scheme or not parsed.netloc:
                    continue
                
                # Check robots.txt rules
                if not self._check_robots_txt(url):
                    logger.info(f"Skipping {url} (disallowed by robots.txt)")
                    continue
                
                # Randomly choose user agent
                headers = {
                    "User-Agent": random.choice(self.USER_AGENTS),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Pragma": "no-cache",
                    "Cache-Control": "no-cache"
                }
                
                # Implement retry logic
                success, content = self._fetch_with_retry(url, headers)
                if not success:
                    continue
                
                # Truncate long content
                if len(content) > 8000:
                    content = content[:8000] + "..."
                
                # Include source
                all_content.append(f"CONTENT FROM {url}:\n{content}\n\n")
                
            except Exception as e:
                logger.warning(f"Failed to scrape {url}: {e}")
                continue
                
        return "\n".join(all_content)
    
    def _fetch_with_retry(self, url: str, headers: Dict[str, str], max_retries: int = 3) -> Tuple[bool, str]:
        """Fetch URL content with retry logic"""
        for attempt in range(max_retries):
            try:
                # Use a session to persist cookies and settings
                session = requests.Session()
                response = session.get(
                    url,
                    headers=headers, 
                    timeout=15,
                    verify=False  # Bypasses SSL verification issues
                )
                
                # Handle HTTP error status codes
                if response.status_code == 403:  # Forbidden
                    logger.warning(f"Access forbidden for {url}, trying with different user agent")
                    headers["User-Agent"] = random.choice(self.USER_AGENTS)
                    continue
                
                if response.status_code in [429, 503]:  # Too many requests or service unavailable
                    wait_time = (2 ** attempt) + random.uniform(0, 1)  # Exponential backoff
                    logger.warning(f"Rate limited on {url}, waiting {wait_time:.2f} seconds")
                    time.sleep(wait_time)
                    continue
                    
                response.raise_for_status()
                
                # Check content type - only process HTML
                content_type = response.headers.get('Content-Type', '').lower()
                if 'text/html' not in content_type:
                    logger.info(f"Skipping non-HTML content: {content_type} for {url}")
                    return False, ""
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract main content, trying various selectors common in tourism websites
                main_content = (
                    soup.find('main') or 
                    soup.find('article') or 
                    soup.find('div', class_=lambda c: c and ('content' in c.lower() or 'main' in c.lower())) or
                    soup.find('body')
                )
                
                if not main_content:
                    logger.warning(f"Could not find main content in {url}")
                    return False, ""
                
                # Remove script, style elements and other non-content elements
                for element in main_content(["script", "style", "nav", "footer", "header", "aside", "form", "iframe"]):
                    element.extract()
                
                # Get text
                text = main_content.get_text(separator="\n", strip=True)
                
                # Clean up the text
                text = re.sub(r'\n\s*\n+', '\n\n', text)  # Replace multiple newlines with just two
                
                return True, text
                
            except requests.exceptions.SSLError:
                logger.warning(f"SSL Error for {url}, trying with relaxed verification")
                try:
                    # Try again with SSL verification disabled
                    session = requests.Session()
                    response = session.get(
                        url,
                        headers=headers,
                        timeout=15, 
                        verify=False
                    )
                    response.raise_for_status()
                    
                    # Process the content as normal
                    soup = BeautifulSoup(response.text, 'html.parser')
                    main_content = soup.find('main') or soup.find('article') or soup.find('body')
                    
                    if not main_content:
                        return False, ""
                        
                    # Clean content
                    for element in main_content(["script", "style", "nav", "footer", "header"]):
                        element.extract()
                    
                    text = main_content.get_text(separator="\n", strip=True)
                    return True, text
                    
                except Exception as e:
                    logger.warning(f"Failed on retry with SSL bypass: {e}")
                    continue
                    
            except (requests.exceptions.RequestException, Exception) as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Error fetching {url} (attempt {attempt+1}/{max_retries}): {e}. Retrying in {wait_time:.2f}s")
                    time.sleep(wait_time)
                else:
                    logger.warning(f"Failed all {max_retries} attempts to fetch {url}: {e}")
                    return False, ""
        
        return False, ""
    
    def chat(self, question: str) -> str:
        """Answer a question about the itinerary"""
        if not self.model:
            return "I'm sorry, but the chat functionality is not available. Please make sure a Gemini API key is provided."
        
        try:
            # Check if this is a general knowledge question
            is_general_question = self._is_general_knowledge_question(question)
            
            # Create context from itinerary and URL contents
            full_context = self.itinerary_text
            
            # Add URL context if it's not too long
            url_context = self.url_contents
            if len(url_context) > 10000:
                url_context = url_context[:10000] + "...(content truncated)"
                
            # Add chat history context (limited to last 5 exchanges)
            history_context = ""
            if self.chat_history:
                history_context = "\n\nPREVIOUS CONVERSATION:\n"
                for i, exchange in enumerate(self.chat_history[-5:]):
                    history_context += f"Q{i+1}: {exchange['question']}\nA{i+1}: {exchange['answer']}\n"
            
            # Create the prompt with all context
            if is_general_question:
                destination_info = f"The traveler is currently planning a trip to {self.destination}. " if self.destination else ""
                
                prompt = f"""You are a helpful travel assistant answering questions about travel and general knowledge.
                {destination_info}The user is asking a general question that isn't directly about their specific itinerary.
                
                {history_context if history_context else ''}
                
                QUESTION: {question}
                
                Please provide an accurate and helpful response. You can use your general knowledge about travel, 
                geography, currencies, culture, and other relevant information to answer this question. 
                Format your response in markdown.
                """
            else:
                prompt = f"""You are a helpful travel assistant answering questions about a specific itinerary. 
                Use ONLY the information provided in the context below and the previous conversation history.
                If the answer is not in the context, say you don't have enough information, but try to be helpful.
    
                CONTEXT:
                {full_context}
                
                {url_context if url_context else ''}
                
                {history_context}
                
                QUESTION: {question}
                
                Provide a helpful, accurate response based primarily on the information above. Format the response in markdown.
                """
            
            # Query the model
            response = self.model.generate_content(prompt)
            answer = response.text
            
            # Save to chat history
            self.chat_history.append({
                "question": question,
                "answer": answer
            })
            
            return answer
            
        except Exception as e:
            logger.error(f"Error in chat response: {e}")
            return f"I encountered an error while processing your question: {str(e)}"
    
    def _is_general_knowledge_question(self, question: str) -> bool:
        """Determine if a question is about general knowledge rather than the specific itinerary"""
        # Keywords that suggest general knowledge questions
        general_keywords = [
            'currency', 'language', 'population', 'weather', 'climate', 'time zone',
            'visa', 'safety', 'best time', 'history of', 'capital of', 'country',
            'how far', 'how many', 'what is', 'where is', 'when was', 'who is'
        ]
        
        # Patterns that suggest itinerary-specific questions
        itinerary_keywords = [
            'itinerary', 'hotel', 'restaurant', 'day', 'visit', 'attraction',
            'schedule', 'plan', 'activity', 'budget', 'cost', 'price', 'expense',
            'transportation', 'travel', 'tour', 'ticket', 'booking'
        ]
        
        # If any itinerary keywords are present, it's likely an itinerary question
        for keyword in itinerary_keywords:
            if keyword in question.lower():
                return False
                
        # If general keywords are present, it might be a general knowledge question
        for keyword in general_keywords:
            if keyword in question.lower():
                return True
                
        # Default to treating it as an itinerary question
        return False
    
    def reset_conversation(self) -> None:
        """Reset the conversation history"""
        self.chat_history = []
        logger.info("Conversation history has been reset")
    
    def create_session(self, prefs=None, narrative=None, budget=None, experiences=None, scores=None, **kwargs):
        """Create a new chat session for an itinerary and return a session ID."""
        import uuid
        session_id = str(uuid.uuid4())
        
        # Store session data
        self.session_data = {
            'session_id': session_id,
            'prefs': prefs,
            'narrative': narrative,
            'budget': budget,
            'experiences': experiences,
            'scores': scores
        }
        
        # Add debug logging
        logger.info(f"Creating chat session {session_id}")
        logger.info(f"API key available: {bool(self.api_key)}")
        
        # Configure Gemini API
        if self.api_key:
            genai.configure(api_key=self.api_key)
        
        # Initialize the model directly - CRITICAL FIX
        try:
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            logger.info(f"Model initialized directly: {bool(self.model)}")
        except Exception as e:
            logger.error(f"Failed to initialize model directly: {e}")
    
        # Initialize the chain with the narrative
        if narrative:
            logger.info(f"Initializing chain with narrative type: {type(narrative)}")
            try:
                # Make sure we're initializing with proper structure
                if isinstance(narrative, dict) and 'main_narrative' in narrative:
                    self.initialize_chain(narrative)
                    logger.info(f"Chain initialized successfully. Model ready: {bool(self.model)}")
                else:
                    # Fix for mismatched narrative format
                    logger.warning(f"Narrative format incorrect: {narrative.keys() if isinstance(narrative, dict) else type(narrative)}")
                    # Try to adapt the format if possible
                    adapted_narrative = {
                        'main_narrative': narrative if isinstance(narrative, str) else str(narrative),
                        'daily_plans': [],
                        'budget_narrative': ''
                    }
                    self.initialize_chain(adapted_narrative)
                    logger.info("Used adapted narrative format")
            except Exception as e:
                logger.error(f"Failed to initialize chain: {e}")
        else:
            logger.warning("No narrative provided for chat initialization")
        
        return session_id

    def answer(self, session_id, user_question):
        """Answer a question in the given session."""
        logger.info(f"Answering question in session {session_id}: {user_question}")
        
        # Check if model is initialized
        if not self.model:
            logger.warning("Model not initialized, attempting to fix...")
            try:
                # Initialize the model
                if self.api_key:
                    genai.configure(api_key=self.api_key)
                    self.model = genai.GenerativeModel('gemini-2.0-flash')
                    logger.info(f"Emergency model initialization successful: {bool(self.model)}")
                else:
                    logger.error("Cannot initialize model: API key missing")
                    return "I'm sorry, but the chat service couldn't be initialized due to a missing API key."
            except Exception as e:
                logger.error(f"Emergency model initialization failed: {e}")
                return "I apologize, but I'm having trouble accessing my knowledge. Please try again later."
    
        # Check if we need to reinitialize the itinerary content
        if not self.itinerary_text and hasattr(self, 'session_data') and self.session_data.get('narrative'):
            logger.info("Reinitializing itinerary context from session data")
            try:
                narrative = self.session_data.get('narrative')
                if narrative:
                    self.initialize_chain(narrative)
                    logger.info(f"Context reinitialized, itinerary text length: {len(self.itinerary_text) if self.itinerary_text else 0}")
                else:
                    logger.warning("No narrative in session data for reinitialization")
            except Exception as e:
                logger.error(f"Failed to reinitialize context: {e}")

        # For debugging: log context availability
        logger.info(f"Context available: itinerary_text={bool(self.itinerary_text)}, URL contents={len(self.url_contents) > 0}, history={len(self.chat_history)}")
        
        # Now try to answer
        result = self.chat(user_question)
        logger.info(f"Answer generated successfully: {bool(result and len(result) > 0)}")
        return result
