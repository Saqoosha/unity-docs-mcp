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
            version: Unity version (will be normalized to major.minor format)
            member_type: Type hint ('property', 'method', 'constructor') to determine URL format
        """
        # Normalize version first
        version = self.normalize_version(version)
        
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
        # Normalize version first
        version = self.normalize_version(version)
        
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
        """Get list of supported Unity versions dynamically from Unity's version info."""
        try:
            # Try to get versions from Unity's UnityVersionsInfo.js
            response = self.session.get("https://docs.unity3d.com/StaticFilesConfig/UnityVersionsInfo.js", timeout=10)
            if response.status_code == 200:
                content = response.text
                
                # Parse both supported and not supported versions
                # Supported versions have active documentation
                # Not supported versions might still have docs but aren't actively maintained
                import re
                
                # Find supported versions array
                supported_pattern = r'supported:\s*\[(.*?)\]'
                supported_match = re.search(supported_pattern, content, re.DOTALL)
                
                # Find not supported versions array
                not_supported_pattern = r'notSupported:\s*\[(.*?)\]'
                not_supported_match = re.search(not_supported_pattern, content, re.DOTALL)
                
                all_versions = []
                
                # Extract supported versions (these are actively maintained)
                if supported_match:
                    supported_content = supported_match.group(1)
                    version_pattern = r'\{\s*major:\s*(\d+),\s*minor:\s*(\d+)(?:,\s*[^}]*)?\s*\}'
                    versions = re.findall(version_pattern, supported_content)
                    for major, minor in versions:
                        all_versions.append(f"{major}.{minor}")
                
                # Extract not supported versions that still have docs (recent ones)
                if not_supported_match:
                    not_supported_content = not_supported_match.group(1)
                    version_pattern = r'\{\s*major:\s*(\d+),\s*minor:\s*(\d+)(?:,\s*[^}]*)?\s*\}'
                    versions = re.findall(version_pattern, not_supported_content)
                    
                    # Only include relatively recent "not supported" versions
                    # that still likely have documentation available
                    recent_cutoff_year = 2019
                    for major, minor in versions:
                        major_int = int(major)
                        # Include Unity 2019+ versions even if marked "not supported"
                        if major_int >= recent_cutoff_year:
                            all_versions.append(f"{major}.{minor}")
                
                if all_versions:
                    # Sort versions with latest first
                    # Convert to comparable format for sorting
                    def version_key(v):
                        parts = v.split('.')
                        major = int(parts[0])
                        minor = int(parts[1]) if len(parts) > 1 else 0
                        return (major, minor)
                    
                    sorted_versions = sorted(all_versions, key=version_key, reverse=True)
                    return sorted_versions
                        
        except Exception as e:
            print(f"Failed to fetch supported versions from Unity: {e}")
        
        # Fallback to hardcoded list if dynamic fetching fails
        return [
            "6000.2", "6000.1", "6000.0",
            "2023.3", "2023.2", "2023.1",
            "2022.3", "2022.2", "2022.1", 
            "2021.3", "2021.2", "2021.1",
            "2020.3", "2020.2", "2020.1",
            "2019.4"
        ]
    
    def get_latest_version(self) -> str:
        """Get the latest Unity version dynamically by checking Unity's redirect.
        
        Unity's docs redirect version-less URLs to the latest version.
        """
        try:
            # Use version-less URL and let Unity redirect to latest
            response = self.session.get("https://docs.unity3d.com/ScriptReference/GameObject.html", timeout=10)
            if response.status_code == 200:
                # Extract version from the redirected URL or page content
                final_url = response.url
                
                # Try to extract version from final URL first
                # Format: https://docs.unity3d.com/6000.1/Documentation/ScriptReference/GameObject.html
                url_version_match = re.search(r'/(\d+\.\d+)/', final_url)
                if url_version_match:
                    return url_version_match.group(1)
                
                # Fallback: extract from page content
                # Look for "Unity 6.1" in the HTML
                content = response.text
                unity_version_match = re.search(r'Unity (\d+\.\d+)', content)
                if unity_version_match:
                    version_str = unity_version_match.group(1)
                    # Convert "6.1" to "6000.1" format if needed
                    if '.' in version_str and len(version_str.split('.')[0]) <= 2:
                        major, minor = version_str.split('.')
                        if len(major) <= 2:  # e.g., "6.1" -> "6000.1"
                            return f"{major}000.{minor}"
                    return version_str
                        
        except Exception as e:
            print(f"Failed to fetch latest version from Unity redirect: {e}")
        
        # Fallback to hardcoded latest
        supported = self.get_supported_versions()
        return supported[0] if supported else "6000.0"
    
    def normalize_version(self, version: str) -> str:
        """Normalize Unity version string to major.minor format.
        
        Examples:
            6000.0.29f1 -> 6000.0
            2022.3.45f1 -> 2022.3  
            2021.3.12a1 -> 2021.3
            6000.0 -> 6000.0 (unchanged)
        """
        # Extract major.minor from version string using regex
        # Matches: 6000.0.29f1, 2022.3.45a1, 2021.3.12b2, etc.
        match = re.match(r'^(\d+\.\d+)', version)
        if match:
            return match.group(1)
        return version  # Return as-is if no match
    
    def validate_version(self, version: str) -> bool:
        """Validate if a Unity version is supported."""
        normalized_version = self.normalize_version(version)
        return normalized_version in self.get_supported_versions()
    
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
    
    def check_api_availability_across_versions(self, class_name: str, method_name: Optional[str] = None) -> Dict[str, List[str]]:
        """Check which Unity versions have the specified API by making HTTP requests.
        
        Args:
            class_name: The Unity class name
            method_name: Optional method/property name
            
        Returns:
            Dictionary with 'available' and 'unavailable' version lists
        """
        available_versions = []
        unavailable_versions = []
        
        # Test a subset of important versions to avoid too many requests
        test_versions = ["6000.0", "2023.3", "2022.3", "2021.3", "2020.3", "2019.4"]
        
        for version in test_versions:
            normalized_version = self.normalize_version(version)
            if self.validate_version(normalized_version):
                url = self._build_api_url(class_name, method_name, normalized_version)
                
                try:
                    response = self.session.head(url, timeout=10)  # HEAD request is faster
                    if response.status_code == 200:
                        available_versions.append(normalized_version)
                    else:
                        unavailable_versions.append(normalized_version)
                except requests.exceptions.RequestException:
                    unavailable_versions.append(normalized_version)
                    
                # Rate limiting
                time.sleep(0.2)
        
        return {
            "available": available_versions,
            "unavailable": unavailable_versions
        }