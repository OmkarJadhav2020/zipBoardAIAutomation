import time
import requests
from bs4 import BeautifulSoup
import config

class Scraper:
    def __init__(self):
        self.session = requests.Session()
        # Pretend to be a browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.last_request_time = 0

    def _rate_limit(self):
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < config.REQUEST_INTERVAL:
            time.sleep(config.REQUEST_INTERVAL - elapsed)
        self.last_request_time = time.time()

    def get_soup(self, url):
        self._rate_limit()
        try:
            print(f"Scraping: {url}")
            response = self.session.get(url)
            if response.status_code == 429:
                print("Rate limited! Waiting 10 seconds...")
                time.sleep(10)
                return self.get_soup(url) # Retry once
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None
            
    def get_categories(self):
        soup = self.get_soup(config.BASE_URL)
        if not soup:
            return []
        
        categories = []
        # User supplied selectors:
        # Category URL: a.category href
        # Category Name: a.category h3 text
        # Article Count: .article-count span text
        
        # We assume .article-count is inside a.category or related to it.
        # Let's try finding all a.category elements
        category_links = soup.select('a.category')
        
        for link in category_links:
            try:
                name_tag = link.select_one('h3')
                name = name_tag.get_text(strip=True) if name_tag else "Unknown"
                
                url = link.get('href')
                if url and not url.startswith('http'):
                    url = config.BASE_URL.rstrip('/') + '/' + url.lstrip('/')
                
                count_tag = link.select_one('.article-count span')
                if not count_tag: # Try checking sibling or parent logic if fails, but assume inside for now
                     count_tag = link.select_one('.article-count')
                
                count_str = count_tag.get_text(strip=True) if count_tag else "0"
                # Extract number from string like "12 articles"
                count = int(''.join(filter(str.isdigit, count_str))) if any(c.isdigit() for c in count_str) else 0
                
                categories.append({
                    'name': name,
                    'url': url,
                    'count': count
                })
            except Exception as e:
                print(f"Error parsing category: {e}")
                
        return categories

    def get_articles_from_category(self, category_url):
        soup = self.get_soup(category_url)
        if not soup:
            return []
            
        articles = []
        # Need to find article links. Usually generic list of links in a help center.
        # Common pattern: <a href="/article/...">Title</a>
        # We will try to find the main list container. 
        # Inspecting might be needed, but let's try a generic approach + user hint if any.
        # User didn't give article list selector, only category one.
        # We will assume standard structure.
        
        # Heuristic: Find all links that look like articles
        links = soup.select('a')
        for link in links:
            href = link.get('href')
            if href and ('article' in href or 'help' in href) and href != '#':
                 # Filter out navigation links if possible
                 # usually title is the text
                 title = link.get_text(strip=True)
                 if not title: continue
                 
                 full_url = href
                 if not full_url.startswith('http'):
                    full_url = config.BASE_URL.rstrip('/') + '/' + full_url.lstrip('/')
                    
                 # heuristic to avoid main page or category links
                 if full_url == category_url or full_url == config.BASE_URL:
                     continue
                     
                 articles.append({
                     'title': title,
                     'url': full_url
                 })
                 
        return articles

    def get_article_content(self, article_url):
        soup = self.get_soup(article_url)
        if not soup:
            return ""
            
        # Get all text from body, assuming article is main content
        # Better: try to find 'article' tag or main div
        article_body = soup.select_one('article')
        if not article_body:
            article_body = soup.select_one('div.article-body') # common class
        if not article_body:
            article_body = soup.find('body')
            
        if article_body:
            # Check for screenshots (img tags)
            images = article_body.find_all('img')
            has_screenshots = len(images) > 0
            
            text = article_body.get_text(separator='\n', strip=True)
            word_count = len(text.split())
            return text, word_count, has_screenshots
        return "", 0, False

    def extract_id_from_url(self, url):
        # Url format: .../article/63-how-to... -> 63
        try:
            import re
            # Match number at start of slug
            # url parts: http://.../article/63-title
            if '/article/' in url:
                slug = url.split('/article/')[1]
                # ID is usually the numeric part before the first hyphen
                match = re.match(r'^(\d+)-', slug)
                if match:
                    return match.group(1)
            return "N/A"
        except:
            return "N/A"
