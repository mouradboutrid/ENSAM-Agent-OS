import urllib.request
import urllib.parse
from html.parser import HTMLParser
import re
import logging

logger = logging.getLogger(__name__)

class DDGHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results = []
        self.current_result = None
        self.current_field = None
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get("class", "")
        
        # Check if we hit a result container div
        # Typically class contains "result" but not "results" (which is container)
        classes = cls.split()
        if tag == "div" and "result" in classes:
            if self.current_result:
                self._save_current()
            self.current_result = {"title": "", "url": "", "snippet": ""}
            
        elif self.current_result is not None:
            if tag == "a" and ("result__a" in classes or "result__url" in classes or "result__a" in cls or "result__url" in cls):
                self.current_field = "title"
                href = attrs_dict.get("href", "")
                if "uddg=" in href:
                    try:
                        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                        if "uddg" in parsed:
                            href = parsed["uddg"][0]
                    except Exception:
                        pass
                self.current_result["url"] = href
            elif "result__snippet" in cls:
                self.current_field = "snippet"
                
    def handle_endtag(self, tag):
        if self.current_field == "title" and tag == "a":
            self.current_field = None
        elif self.current_field == "snippet" and tag in ("a", "span", "div"):
            self.current_field = None
            
    def handle_data(self, data):
        if self.current_result is not None and self.current_field:
            self.current_result[self.current_field] += data

    def _save_current(self):
        if self.current_result and (self.current_result["url"] or self.current_result["title"]):
            self.current_result["title"] = self.current_result["title"].strip()
            self.current_result["snippet"] = self.current_result["snippet"].strip()
            self.current_result["title"] = re.sub(r'\s+', ' ', self.current_result["title"])
            self.current_result["snippet"] = re.sub(r'\s+', ' ', self.current_result["snippet"])
            self.results.append(self.current_result)
        self.current_result = None

    def close(self):
        super().close()
        if self.current_result:
            self._save_current()

def search_web_ddg(query: str, max_results: int = 4) -> str:
    """
    Performs a zero-dependency web search using DuckDuckGo HTML.
    Returns a formatted string of results suitable for LLM injection.
    """
    if not query or not query.strip():
        return "No search query provided."
        
    url = "https://html.duckduckgo.com/html/"
    params = {"q": query}
    data = urllib.parse.urlencode(params).encode("utf-8")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as response:
            html_content = response.read().decode("utf-8")
            
        parser = DDGHTMLParser()
        parser.feed(html_content)
        parser.close()
        
        results = parser.results[:max_results]
        if not results:
            return f"No search results found on DuckDuckGo for: '{query}'"
            
        formatted_results = [f"Web Search Results for '{query}':"]
        for idx, res in enumerate(results, 1):
            formatted_results.append(
                f"[{idx}] Title: {res['title']}\n    URL: {res['url']}\n    Snippet: {res['snippet']}"
            )
            
        return "\n\n".join(formatted_results)
        
    except Exception as e:
        logger.error(f"Error performing web search: {e}", exc_info=True)
        return f"⚠️ Web search failed for query '{query}': {str(e)}"
