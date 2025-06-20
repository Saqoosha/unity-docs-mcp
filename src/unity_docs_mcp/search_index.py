"""Unity documentation search index handler."""

import re
import json
from typing import List, Dict, Set, Tuple, Optional
import requests
from collections import defaultdict
import time
import os
import pickle
from datetime import datetime, timedelta


class UnitySearchIndex:
    """Handles Unity documentation search using pre-built index files."""

    def __init__(self, cache_dir: Optional[str] = None, cache_duration_hours: int = 24):
        self.pages = []
        self.page_info = []
        self.search_index = {}
        self.common_words = set()
        self._loaded = False
        self._memory_cache = {}
        self.cache_duration = timedelta(hours=cache_duration_hours)

        # Set up file cache directory
        if cache_dir:
            self.cache_dir = cache_dir
        else:
            # Default to user's cache directory
            home = os.path.expanduser("~")
            self.cache_dir = os.path.join(home, ".unity_docs_mcp", "cache")

        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, version: str) -> str:
        """Get cache file path for a specific version."""
        return os.path.join(self.cache_dir, f"search_index_{version}.pkl")

    def _load_from_cache(self, version: str) -> bool:
        """Try to load index from cache file."""
        cache_path = self._get_cache_path(version)

        if os.path.exists(cache_path):
            try:
                # Check if cache is still valid
                cache_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
                if datetime.now() - cache_time < self.cache_duration:
                    with open(cache_path, "rb") as f:
                        cache_data = pickle.load(f)
                        self.pages = cache_data["pages"]
                        self.page_info = cache_data["page_info"]
                        self.search_index = cache_data["search_index"]
                        self.common_words = cache_data["common_words"]
                        return True
            except Exception:
                # Cache load failed, will re-download
                pass

        return False

    def _save_to_cache(self, version: str) -> None:
        """Save index to cache file."""
        cache_path = self._get_cache_path(version)

        try:
            cache_data = {
                "pages": self.pages,
                "page_info": self.page_info,
                "search_index": self.search_index,
                "common_words": self.common_words,
                "version": version,
                "timestamp": datetime.now(),
            }

            with open(cache_path, "wb") as f:
                pickle.dump(cache_data, f)
        except Exception:
            # Cache save failed, non-critical
            pass

    def load_index(self, version: str = "6000.0", force_refresh: bool = False) -> bool:
        """Load search index from Unity documentation."""
        # Check memory cache first
        cache_key = f"index_{version}"
        if cache_key in self._memory_cache and not force_refresh:
            self.pages, self.page_info, self.search_index, self.common_words = (
                self._memory_cache[cache_key]
            )
            self._loaded = True
            return True

        # Try to load from file cache if not forcing refresh
        if not force_refresh and self._load_from_cache(version):
            # Also store in memory cache
            self._memory_cache[cache_key] = (
                self.pages,
                self.page_info,
                self.search_index,
                self.common_words,
            )
            self._loaded = True
            return True

        try:
            # Download index.js
            index_url = f"https://docs.unity3d.com/{version}/Documentation/ScriptReference/docdata/index.js"
            response = requests.get(index_url, timeout=30)

            if response.status_code != 200:
                return False

            # Parse the JavaScript file
            content = response.text

            # Parse the JavaScript file line by line
            lines = content.split("\n")
            current_var = None
            current_content = []

            for line in lines:
                if line.startswith("var pages = "):
                    current_var = "pages"
                    current_content = []
                elif line.startswith("var info = "):
                    # Process pages
                    if current_content:
                        array_str = "".join(current_content).strip().rstrip(";")
                        self.pages = json.loads(array_str)
                    current_var = "info"
                    current_content = []
                elif line.startswith("var common = "):
                    # Process info
                    if current_content:
                        array_str = "".join(current_content).strip().rstrip(";")
                        self.page_info = json.loads(array_str)
                    current_var = "common"
                    current_content = []
                elif line.startswith("var searchIndex = "):
                    # Process common
                    if current_content:
                        obj_str = "".join(current_content).strip().rstrip(";")
                        common_dict = json.loads(obj_str)
                        self.common_words = set(common_dict.keys())
                    current_var = "searchIndex"
                    current_content = []
                elif current_var:
                    current_content.append(line)

            # Process the last variable (searchIndex)
            if current_var == "searchIndex" and current_content:
                obj_str = "".join(current_content).strip().rstrip(";")
                if obj_str.endswith("}"):
                    self.search_index = json.loads(obj_str)

            # Save to both memory and file cache
            self._memory_cache[cache_key] = (
                self.pages,
                self.page_info,
                self.search_index,
                self.common_words,
            )
            self._save_to_cache(version)
            self._loaded = True

            return True

        except Exception:
            # Failed to load search index
            return False

    def clear_cache(self, version: Optional[str] = None) -> None:
        """Clear cache for a specific version or all versions."""
        if version:
            # Clear specific version
            cache_path = self._get_cache_path(version)
            if os.path.exists(cache_path):
                os.remove(cache_path)

            # Clear from memory cache
            cache_key = f"index_{version}"
            if cache_key in self._memory_cache:
                del self._memory_cache[cache_key]
        else:
            # Clear all caches
            for file in os.listdir(self.cache_dir):
                if file.startswith("search_index_") and file.endswith(".pkl"):
                    os.remove(os.path.join(self.cache_dir, file))

            # Clear memory cache
            self._memory_cache.clear()

    def _detect_member_type(self, url_name: str) -> str:
        """Detect whether a Unity documentation entry is a property, method, or class.

        Args:
            url_name: The URL component (e.g., 'GameObject-transform', 'GameObject.SetActive')

        Returns:
            One of: 'property', 'method', 'constructor', 'class'
        """
        # Special case: constructors
        if "-ctor" in url_name:
            return "constructor"

        # Hyphen indicates property (or event/delegate which we treat as property)
        if "-" in url_name:
            return "property"

        # No dots or hyphens = simple class
        if "." not in url_name:
            return "class"

        # Has dots - distinguish between methods and nested classes
        parts = url_name.split(".")

        # Known nested class patterns (namespaces)
        namespace_patterns = [
            "UnityEngine",
            "UnityEditor",
            "Unity",
            "System",
            "EditorSettings",
            "PlayerSettings",
            "BuildSettings",
        ]

        # Check if it's a namespace.Class pattern
        if len(parts) == 2:
            # If first part is a known namespace and second part starts with uppercase
            if parts[0] in namespace_patterns and parts[1] and parts[1][0].isupper():
                return "class"

            # If both parts start with uppercase, could be nested class
            # But most likely it's a method if second part is a common method name
            if all(p and p[0].isupper() for p in parts):
                # Common method name patterns
                method_patterns = [
                    "Get",
                    "Set",
                    "Add",
                    "Remove",
                    "Clear",
                    "Contains",
                    "Find",
                    "Load",
                    "Save",
                    "Create",
                    "Delete",
                    "Update",
                    "Is",
                    "Has",
                    "Can",
                    "Should",
                    "Try",
                    "Move",
                    "Rotate",
                    "Transform",
                    "Convert",
                    "Parse",
                    "ToString",
                    "Equals",
                ]

                # Check if second part starts with a method pattern
                second_part = parts[1]
                for pattern in method_patterns:
                    if second_part.startswith(pattern):
                        return "method"

                # Default to class for other uppercase patterns
                return "class"

        # Three or more parts, or single uppercase after dot = method
        return "method"

    def search(
        self, query: str, version: str = "6000.0", max_results: int = 20
    ) -> List[Dict[str, str]]:
        """Search Unity documentation using the loaded index."""
        if not self._loaded or version not in [
            key.split("_")[1] for key in self._memory_cache.keys()
        ]:
            if not self.load_index(version):
                return []

        # Process query
        query = query.strip()
        query_lower = query.lower()

        # Score pages with improved algorithm
        page_scores = {}

        # Phase 1: Look for exact class matches
        for page_idx, page in enumerate(self.pages):
            if page_idx < len(self.page_info):
                page_name = page[0]
                page_title = page[1] if len(page) > 1 else page_name
                member_type = self._detect_member_type(page_name)

                # Calculate score based on match quality
                score = 0

                # Apply Unity's scoring algorithm
                title_lower = page_title.lower()

                # Exact match on title (Unity gives +10000)
                if title_lower == query_lower:
                    score = 10000

                # Class name exact match (after namespace)
                elif member_type == "class":
                    # Check if class name part matches exactly
                    if "." in page_name:
                        class_part = page_name.split(".")[-1]
                        if class_part.lower() == query_lower:
                            score = 5000  # Very high but less than exact
                    elif page_name.lower() == query_lower:
                        score = 5000

                # Title contains query at word boundary (Unity gives +500 for start/end)
                elif query_lower in title_lower:
                    placement = title_lower.index(query_lower)
                    # At start or after '.'
                    if placement == 0 or (
                        placement > 0 and title_lower[placement - 1] == "."
                    ):
                        score = 1500
                    # At end or before '.'
                    elif placement + len(query_lower) == len(title_lower) or (
                        placement + len(query_lower) < len(title_lower)
                        and title_lower[placement + len(query_lower)] == "."
                    ):
                        score = 1500
                    else:
                        score = 500

                # Member of a matching class
                elif "." in page_name or "-" in page_name:
                    # Extract base class name
                    base_name = (
                        page_name.split(".")[0]
                        if "." in page_name
                        else page_name.split("-")[0]
                    )
                    if "." in base_name:
                        # Has namespace
                        class_part = base_name.split(".")[-1]
                        if class_part.lower() == query_lower:
                            score = 800 if member_type == "property" else 700
                    elif base_name.lower() == query_lower:
                        score = 850

                # Partial matches
                if score == 0:
                    page_name_lower = page_name.lower()
                    if query_lower in page_name_lower:
                        # Boost if it's a word boundary match
                        if (
                            page_name_lower.startswith(query_lower)
                            or f".{query_lower}" in page_name_lower
                        ):
                            score = 300
                        elif f"-{query_lower}" in page_name_lower:
                            score = 250
                        else:
                            score = 100

                if score > 0:
                    page_scores[page_idx] = score

        # Sort by score
        sorted_results = sorted(page_scores.items(), key=lambda x: x[1], reverse=True)

        # Build results
        results = []
        for page_idx, score in sorted_results[:max_results]:
            if page_idx < len(self.pages) and page_idx < len(self.page_info):
                page_name = self.pages[page_idx][0]
                page_title = (
                    self.pages[page_idx][1]
                    if len(self.pages[page_idx]) > 1
                    else page_name
                )
                page_description = (
                    self.page_info[page_idx][0] if self.page_info[page_idx] else ""
                )

                # Detect member type
                member_type = self._detect_member_type(page_name)

                # Build URL
                url = f"https://docs.unity3d.com/{version}/Documentation/ScriptReference/{page_name}.html"

                results.append(
                    {
                        "title": page_title,
                        "url": url,
                        "description": (
                            page_description[:200] + "..."
                            if len(page_description) > 200
                            else page_description
                        ),
                        "type": member_type,
                    }
                )

        return results

    def suggest_classes(self, partial_name: str, max_results: int = 10) -> List[str]:
        """Suggest Unity class names based on partial input."""
        if not self._loaded:
            if not self.load_index():
                return []

        partial_lower = partial_name.lower()
        suggestions = []

        for page in self.pages:
            if len(page) > 1:
                page_name = page[0]
                page_title = page[1]

                # Only consider class pages (not methods)
                if "." not in page_name and "-" not in page_name:
                    if partial_lower in page_title.lower():
                        suggestions.append(page_title)
                        if len(suggestions) >= max_results:
                            break

        return suggestions
