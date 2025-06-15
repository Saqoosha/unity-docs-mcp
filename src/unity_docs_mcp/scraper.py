"""Web scraping utilities for Unity documentation."""

import requests
import re
from typing import Optional, Dict, List
from urllib.parse import urljoin, quote
import time
from .search_index import UnitySearchIndex


class UnityDocScraper:
    """Scraper for Unity documentation websites."""
    
    def __init__(self):
        self.base_url = "https://docs.unity3d.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.rate_limit_delay = 0.5  # seconds between requests
        self.last_request_time = 0
        self.search_index = UnitySearchIndex()
    
    def get_api_doc(self, class_name: str, method_name: Optional[str] = None, version: str = "6000.0", member_type: Optional[str] = None) -> Dict[str, str]:
        """Fetch Unity API documentation for a specific class or method.
        
        Args:
            class_name: The Unity class name
            method_name: The method or property name (optional)
            version: Unity version
            member_type: Type hint ('property', 'method', 'constructor') to determine URL format
        """
        try:
            # Determine URL format based on member type
            if method_name and member_type:
                # Use type information to build correct URL immediately
                use_hyphen = member_type in ['property', 'constructor']
                url = self._build_api_url(class_name, method_name, version, use_hyphen=use_hyphen)
                html_content = self._fetch_page(url)
            elif method_name:
                # No type info provided, try both formats (old behavior)
                # First try with dot notation (for methods)
                url = self._build_api_url(class_name, method_name, version)
                html_content = self._fetch_page(url)
                
                # If that fails, try with hyphen notation (for properties)
                if not html_content:
                    property_url = self._build_api_url(class_name, method_name, version, use_hyphen=True)
                    html_content = self._fetch_page(property_url)
                    if html_content:
                        url = property_url  # Update URL to the one that worked
            else:
                # Just a class name
                url = self._build_api_url(class_name, None, version)
                html_content = self._fetch_page(url)
            
            if html_content:
                return {"url": url, "html": html_content, "status": "success"}
            else:
                return {"error": f"Failed to fetch content from {url}", "status": "error"}
                
        except Exception as e:
            return {"error": f"Error fetching API doc: {str(e)}", "status": "error"}
    
    def search_docs(self, query: str, version: str = "6000.0") -> Dict[str, any]:
        """Search Unity documentation using local index."""
        try:
            # Use search index for searching
            results = self.search_index.search(query, version)
            
            return {
                "results": results,
                "count": len(results),
                "status": "success"
            }
                
        except Exception as e:
            return {"error": f"Error searching docs: {str(e)}", "status": "error"}
    
    def _build_api_url(self, class_name: str, method_name: Optional[str], version: str, use_hyphen: bool = False) -> str:
        """Build Unity API documentation URL.
        
        Args:
            class_name: The Unity class name
            method_name: The method or property name (optional)
            version: Unity version
            use_hyphen: If True, use hyphen notation (for properties), otherwise use dot notation (for methods)
        """
        # Clean class name
        class_name = class_name.strip()
        
        if method_name:
            method_name = method_name.strip()
            if use_hyphen:
                page_name = f"{class_name}-{method_name}.html"
            else:
                page_name = f"{class_name}.{method_name}.html"
        else:
            page_name = f"{class_name}.html"
        
        return f"{self.base_url}/{version}/Documentation/ScriptReference/{page_name}"
    
    def _build_search_url(self, query: str, version: str) -> str:
        """Build Unity documentation search URL."""
        encoded_query = quote(query.strip())
        return f"{self.base_url}/{version}/Documentation/ScriptReference/30_search.html?q={encoded_query}"
    
    def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch a web page with rate limiting and error handling."""
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        
        try:
            response = self.session.get(url, timeout=30)
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                return response.text
            elif response.status_code == 404:
                return None  # Page not found
            else:
                print(f"HTTP {response.status_code} when fetching {url}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed for {url}: {str(e)}")
            return None
    
    def get_supported_versions(self) -> List[str]:
        """Get list of supported Unity versions."""
        # Common Unity versions - could be expanded by scraping the main docs page
        return [
            "6000.0",
            "2023.3", 
            "2023.2",
            "2023.1",
            "2022.3",
            "2022.2",
            "2022.1",
            "2021.3"
        ]
    
    def validate_version(self, version: str) -> bool:
        """Validate if a Unity version is supported."""
        return version in self.get_supported_versions()
    
    def suggest_class_names(self, partial_name: str) -> List[str]:
        """Suggest Unity class names based on partial input using search index."""
        # Try to use search index first
        suggestions = self.search_index.suggest_classes(partial_name)
        
        if suggestions:
            return suggestions[:10]
        
        # Fallback to common classes if index not loaded
        common_classes = [
            "GameObject", "Transform", "Component", "MonoBehaviour", "Rigidbody",
            "Collider", "Camera", "Light", "AudioSource", "Renderer", "Material",
            "Texture", "Mesh", "Animation", "Animator", "Canvas", "RectTransform",
            "Button", "Text", "Image", "Slider", "ScrollRect", "Input", "Time",
            "Physics", "Mathf", "Vector3", "Vector2", "Quaternion", "Color",
            "Debug", "Application", "Scene", "SceneManager", "Resources",
            "PlayerPrefs", "Coroutine", "WaitForSeconds", "Random"
        ]
        
        partial_lower = partial_name.lower()
        suggestions = [cls for cls in common_classes 
                      if partial_lower in cls.lower()]
        
        return sorted(suggestions)[:10]  # Return top 10 matches