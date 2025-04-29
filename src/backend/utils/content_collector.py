import os
import re
from typing import Dict, List, Set
from pathlib import Path

class ContentCollector:
    def __init__(self, root_dir: str = "src"):
        self.root_dir = root_dir
        self.text_patterns = {
            'js': r'["\']([^"\']+)["\']',  # JavaScript string literals
            'jsx': r'["\']([^"\']+)["\']',  # JSX string literals
            'html': r'>([^<]+)<',  # HTML text content
            'py': r'["\']([^"\']+)["\']',  # Python string literals
        }
        self.ignore_patterns = [
            r'^[0-9]+$',  # Numbers
            r'^[a-zA-Z_][a-zA-Z0-9_]*$',  # Variable names
            r'^[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*$',  # Object properties
            r'^[a-zA-Z_][a-zA-Z0-9_]*\([^)]*\)$',  # Function calls
        ]

    def _should_ignore(self, text: str) -> bool:
        """Check if text should be ignored"""
        return any(re.match(pattern, text) for pattern in self.ignore_patterns)

    def _extract_text_from_file(self, file_path: str) -> Set[str]:
        """Extract text content from a file"""
        texts = set()
        file_ext = os.path.splitext(file_path)[1][1:]
        
        if file_ext not in self.text_patterns:
            return texts

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            pattern = self.text_patterns[file_ext]
            matches = re.finditer(pattern, content)
            
            for match in matches:
                text = match.group(1).strip()
                if text and not self._should_ignore(text):
                    texts.add(text)
                    
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            
        return texts

    def collect_content(self) -> Dict[str, str]:
        """Collect all text content from the app"""
        content = {}
        processed_files = 0
        
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1][1:]
                
                if file_ext in self.text_patterns:
                    texts = self._extract_text_from_file(file_path)
                    for text in texts:
                        # Use the text as both key and value for initial collection
                        content[text] = text
                    processed_files += 1
        
        print(f"Processed {processed_files} files and found {len(content)} unique text strings")
        return content

    def update_content(self, existing_content: Dict[str, str]) -> Dict[str, str]:
        """Update existing content with new text found in the app"""
        new_content = self.collect_content()
        updated_content = existing_content.copy()
        
        # Add new content
        for key, value in new_content.items():
            if key not in updated_content:
                updated_content[key] = value
                
        return updated_content

# Create a singleton instance
content_collector = ContentCollector() 