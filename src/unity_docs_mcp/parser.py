"""HTML parsing utilities for Unity documentation."""

from bs4 import BeautifulSoup, NavigableString
import re
from typing import Dict, List, Optional, Any
from markdownify import markdownify as md
import trafilatura


class UnityDocParser:
    """Parser for Unity documentation HTML content."""
    
    def __init__(self):
        # Configure markdownify options
        self.md_options = {
            'heading_style': 'ATX',
            'bullets': '-',
            'strip': ['script', 'style', 'meta', 'link']
        }
    
    def parse_api_doc(self, html_content: str, url: str) -> Dict[str, Any]:
        """Parse Unity API documentation HTML into structured data."""
        try:
            # Pre-process HTML: Remove all link tags to prevent bracket issues
            cleaned_html = self._remove_link_tags(html_content)
            
            # First try Trafilatura for main content extraction
            trafilatura_content = trafilatura.extract(
                cleaned_html, 
                output_format="markdown",
                include_formatting=True,
                include_links=False,  # Keep disabled as extra safety
                include_images=False,  # Unity docs don't need images for API reference
                include_tables=True,
                url=url
            )
            
            # Clean up the content to fix any remaining formatting issues
            if trafilatura_content:
                trafilatura_content = self._clean_trafilatura_content(trafilatura_content)
                
            # Remove markdown formatting from the content (after other cleaning)
            if trafilatura_content:
                trafilatura_content = self._remove_markdown_formatting(trafilatura_content)
            
            # Fallback to manual parsing if trafilatura fails or returns too little content
            if not trafilatura_content or len(trafilatura_content.strip()) < 100:
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract title
                title = self._extract_title(soup)
                
                # Extract main content manually
                content = self._extract_main_content(soup)
                
                # Convert to markdown
                markdown_content = self._html_to_markdown(content) if content else ""
                
                # Extract additional metadata
                metadata = self._extract_metadata(soup)
                
                # Remove markdown formatting from fallback content too
                markdown_content = self._remove_markdown_formatting(markdown_content)
                
                return {
                    "title": title,
                    "content": markdown_content,
                    "url": url,
                    "metadata": metadata
                }
            else:
                # Use trafilatura result
                soup = BeautifulSoup(html_content, 'html.parser')
                title = self._extract_title(soup)
                metadata = self._extract_metadata(soup)
                
                return {
                    "title": title,
                    "content": trafilatura_content,
                    "url": url,
                    "metadata": metadata
                }
            
        except Exception as e:
            return {"error": f"Failed to parse API documentation: {str(e)}"}
    
    def parse_search_results(self, html_content: str) -> Dict[str, Any]:
        """Parse Unity documentation search results."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find search results container
            results = []
            
            # Look for search result elements (Unity uses different structures)
            search_results = soup.find_all(['div', 'li'], class_=re.compile(r'search|result'))
            
            if not search_results:
                # Try alternative selectors
                search_results = soup.find_all('a', href=re.compile(r'ScriptReference'))
            
            for result in search_results[:20]:  # Limit to 20 results
                result_data = self._extract_search_result(result)
                if result_data:
                    results.append(result_data)
            
            return {
                "results": results,
                "count": len(results)
            }
            
        except Exception as e:
            return {"error": f"Failed to parse search results: {str(e)}"}
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title from HTML."""
        # Unity-specific title selectors
        unity_title_selectors = [
            'h1.heading.inherit',  # Unity API docs main heading
            '.section h1',  # Section heading
            'h1',  # Any h1 tag
        ]
        
        for selector in unity_title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title and title != "Unity - Scripting API" and len(title) < 100:
                    return title
        
        # Fallback to page title
        title_elem = soup.select_one('title')
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            # Extract class name from "Unity - Scripting API: ClassName"
            if ":" in title_text:
                return title_text.split(":")[-1].strip()
        
        return "Unity Documentation"
    
    def _extract_main_content(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Extract main content area from HTML."""
        # Unity-specific selectors based on actual HTML structure
        unity_content_selectors = [
            '#content-wrap .content',  # Unity docs main content
            '.content-block .content .section',  # Unity docs section
            '.content-block .content',  # Unity docs content block
            '#content-wrap',  # Unity content wrapper
            '.section',  # Unity section
        ]
        
        for selector in unity_content_selectors:
            content = soup.select_one(selector)
            if content:
                # Clean up the content
                return self._clean_content(content)
        
        # Fallback selectors
        fallback_selectors = [
            '.content',
            '.main-content', 
            '.documentation',
            'main',
            'body'
        ]
        
        for selector in fallback_selectors:
            content = soup.select_one(selector)
            if content:
                return self._clean_content(content)
        
        return soup
    
    def _clean_content(self, content: BeautifulSoup) -> BeautifulSoup:
        """Clean HTML content by removing unnecessary elements."""
        # Remove navigation, ads, and other non-content elements
        unwanted_selectors = [
            # General unwanted elements
            'nav', '.nav', '.navigation',
            '.sidebar', '.side-panel',
            '.header', '.footer',
            '.breadcrumb', '.breadcrumbs',
            '.advertisement', '.ads',
            'script', 'style', 'meta', 'link',
            '.search-box', '.search-form',
            
            # Unity-specific unwanted elements
            '.feedback',
            '.scrollToFeedback',
            '.switch-link',
            '.clear',
            '#scrollToFeedback',
            '.signature-CS.sig-block span[style*="color:red"]',  # Empty red spans
            '.version-number',
            '.toolbar',
            '.lang-switcher',
        ]
        
        for selector in unwanted_selectors:
            for elem in content.select(selector):
                elem.decompose()
        
        # Remove empty divs and spans
        for elem in content.find_all(['div', 'span']):
            if not elem.get_text(strip=True) and not elem.find_all():
                elem.decompose()
        
        return content
    
    def _html_to_markdown(self, html_content: BeautifulSoup) -> str:
        """Convert HTML to markdown."""
        # Convert to string first
        html_str = str(html_content)
        
        # Use markdownify to convert
        markdown = md(html_str, **self.md_options)
        
        # Clean up the markdown
        markdown = self._clean_markdown(markdown)
        
        return markdown
    
    def _clean_markdown(self, markdown: str) -> str:
        """Clean up markdown content."""
        # Remove excessive whitespace
        markdown = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown)
        
        # Remove empty links
        markdown = re.sub(r'\[\]\([^)]*\)', '', markdown)
        
        # Clean up code blocks
        markdown = re.sub(r'```\s*\n\s*```', '', markdown)
        
        # Remove trailing whitespace
        lines = [line.rstrip() for line in markdown.split('\n')]
        markdown = '\n'.join(lines)
        
        return markdown.strip()
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract metadata from the page."""
        metadata = {}
        
        # Try to extract class name
        class_name_elem = soup.select_one('.class-name, .type-name, h1')
        if class_name_elem:
            metadata['class_name'] = class_name_elem.get_text(strip=True)
        
        # Extract namespace
        namespace_elem = soup.select_one('.namespace')
        if namespace_elem:
            metadata['namespace'] = namespace_elem.get_text(strip=True)
        
        # Extract inheritance info
        inheritance_elem = soup.select_one('.inheritance, .inherits')
        if inheritance_elem:
            metadata['inheritance'] = inheritance_elem.get_text(strip=True)
        
        return metadata
    
    def _extract_search_result(self, result_elem) -> Optional[Dict[str, str]]:
        """Extract data from a single search result element."""
        try:
            result_data = {}
            
            # Extract title/link
            link_elem = result_elem.find('a')
            if link_elem:
                result_data['title'] = link_elem.get_text(strip=True)
                href = link_elem.get('href')
                if href:
                    # Convert relative URLs to absolute
                    if href.startswith('/'):
                        result_data['url'] = f"https://docs.unity3d.com{href}"
                    else:
                        result_data['url'] = href
            else:
                # If no link, use the element text as title
                result_data['title'] = result_elem.get_text(strip=True)
            
            # Extract description (if available)
            desc_elem = result_elem.find(['p', 'div'], class_=re.compile(r'desc|summary'))
            if desc_elem:
                result_data['description'] = desc_elem.get_text(strip=True)
            
            # Only return if we have at least a title
            if result_data.get('title'):
                return result_data
            
        except Exception as e:
            # Skip this result if parsing fails
            pass
        
        return None
    
    def _clean_trafilatura_content(self, content: str) -> str:
        """Clean up trafilatura content to fix code formatting issues."""
        # Fix Unity-specific link bracket issues in code
        
        # Fix inheritance: :[MonoBehaviour] -> : MonoBehaviour
        content = re.sub(r':\s*\[([A-Z][a-zA-Z0-9_]*)\]', r': \1', content)
        
        # Fix variable type declarations: private[GameObject][] -> private GameObject[]
        content = re.sub(r'(\w+)\s*\[([A-Z][a-zA-Z0-9_]*)\]\[\]', r'\1 \2[]', content)
        
        # Fix array creation: new[GameObject][10] -> new GameObject[10]
        content = re.sub(r'new\s*\[([A-Z][a-zA-Z0-9_]*)\]\[', r'new \1[', content)
        
        # Fix method signatures: void[Update]() -> void Update()
        content = re.sub(r'(\w+)\s*\[([A-Z][a-zA-Z0-9_]*)\]\s*\(', r'\1 \2(', content)
        
        # Fix variable declarations: [Vector3]pos -> Vector3 pos
        content = re.sub(r'\[([A-Z][a-zA-Z0-9_]*)\]([a-z][a-zA-Z0-9_]*)', r'\1 \2', content)
        
        # Fix constructor calls: new[Vector3] -> new Vector3
        content = re.sub(r'new\s*\[([A-Z][a-zA-Z0-9_]*)\]', r'new \1', content)
        
        # Fix assignment operations: =[GameObject.CreatePrimitive] -> = GameObject.CreatePrimitive
        content = re.sub(r'=\s*\[([A-Z][a-zA-Z0-9_]*\.[A-Z][a-zA-Z0-9_]*)\]', r'= \1', content)
        
        # Fix static method calls: [Random.Range] -> Random.Range
        content = re.sub(r'=\s*\[([A-Z][a-zA-Z0-9_]*\.[A-Z][a-zA-Z0-9_]*)\]', r'= \1', content)
        
        # Fix property access: +=[Time.deltaTime] -> += Time.deltaTime
        content = re.sub(r'\+=\s*\[([A-Z][a-zA-Z0-9_]*\.[a-zA-Z][a-zA-Z0-9_]*)\]', r'+= \1', content)
        
        # Fix enum values: [PrimitiveType.Cube] -> PrimitiveType.Cube
        content = re.sub(r'\[([A-Z][a-zA-Z0-9_]*\.[A-Z][a-zA-Z0-9_]*)\]', r'\1', content)
        
        # Fix general class references that are alone: [ClassName] -> ClassName (but not in links)
        content = re.sub(r'(?<!\])\[([A-Z][a-zA-Z0-9_]*)\](?!\()', r'\1', content)
        
        return content
    
    def _remove_link_tags(self, html_content: str) -> str:
        """Remove all <a> tags from HTML but keep the text content."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove Unity feedback/UI elements that are not part of API documentation
            self._remove_unity_ui_elements(soup)
            
            # Find all <a> tags and replace them with their text content
            for link in soup.find_all('a'):
                # Replace the <a> tag with just its text content
                link.replace_with(link.get_text())
            
            # Remove bold/strong tags but keep content
            for bold_tag in soup.find_all(['strong', 'b']):
                bold_tag.replace_with(bold_tag.get_text())
            
            return str(soup)
            
        except Exception as e:
            # If parsing fails, fall back to regex approach
            import re
            # Remove <a> tags but keep their content
            return re.sub(r'<a[^>]*>(.*?)</a>', r'\1', html_content, flags=re.IGNORECASE | re.DOTALL)
    
    def _remove_unity_ui_elements(self, soup: BeautifulSoup) -> None:
        """Remove Unity-specific UI elements that are not part of API documentation."""
        # Elements to remove entirely (including content)
        unwanted_selectors = [
            # Feedback related elements
            '.feedback',
            '.feedback-form',
            '.feedback-buttons',
            '.scrollToFeedback',
            '#scrollToFeedback',
            
            # Success/submission messages
            '.submission-success',
            '.submission-failed',
            '.submission-message',
            
            # Version switcher and navigation
            '.version-switcher',
            '.version-number',
            '.otherversionscontent',
            '.versionSwitcherArrow',
            
            # Language switcher
            '.lang-switcher',
            '.lang-list',
            
            # Navigation elements
            '.breadcrumb',
            '.breadcrumbs',
            '.toolbar',
            '.header-wrapper',
            '.navigation',
            
            # Other UI elements
            '.switch-link',
            '.clear',
        ]
        
        for selector in unwanted_selectors:
            for element in soup.select(selector):
                element.decompose()
        
        # Remove elements containing specific feedback text
        feedback_text_patterns = [
            'Leave feedback',
            'Suggest a change',
            'Success!',
            'Thank you for helping us improve',
            'Submission failed',
            'try again',
            'Close',
            'Although we cannot accept all submissions'
        ]
        
        # Remove any element that contains these phrases
        for element in soup.find_all(text=True):
            if any(pattern in element.string for pattern in feedback_text_patterns if element.string):
                # Remove the parent element
                parent = element.parent
                if parent and parent.name not in ['html', 'body']:
                    parent.decompose()
    
    def _remove_markdown_formatting(self, content: str) -> str:
        """Remove markdown formatting (bold, links) from content."""
        import re
        
        # Remove **bold** formatting
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
        
        # Remove __bold__ formatting  
        content = re.sub(r'__(.*?)__', r'\1', content)
        
        # Remove markdown links but keep the text: [text](url) -> text
        content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
        
        # Remove single * emphasis if desired (optional)
        # content = re.sub(r'\*(.*?)\*', r'\1', content)
        
        return content