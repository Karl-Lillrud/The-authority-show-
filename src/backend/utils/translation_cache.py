import json
import os
from typing import Dict, Optional
from datetime import datetime, timedelta

class TranslationCache:
    def __init__(self, cache_dir: str = "translation_cache"):
        self.cache_dir = cache_dir
        self.cache_expiry = timedelta(days=7)  # Cache expires after 7 days
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        """Ensure the cache directory exists"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def _get_cache_path(self, language: str) -> str:
        """Get the cache file path for a language"""
        return os.path.join(self.cache_dir, f"{language}.json")

    def get_cached_translations(self, language: str) -> Optional[Dict]:
        """Get cached translations for a language"""
        cache_path = self._get_cache_path(language)
        
        if not os.path.exists(cache_path):
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                
            # Check if cache is expired
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cache_time > self.cache_expiry:
                return None
                
            return cache_data['translations']
        except Exception:
            return None

    def cache_translations(self, language: str, translations: Dict):
        """Cache translations for a language"""
        cache_path = self._get_cache_path(language)
        
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'translations': translations
        }
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to cache translations: {e}")

    def clear_cache(self, language: Optional[str] = None):
        """Clear cache for a specific language or all languages"""
        if language:
            cache_path = self._get_cache_path(language)
            if os.path.exists(cache_path):
                os.remove(cache_path)
        else:
            for file in os.listdir(self.cache_dir):
                if file.endswith('.json'):
                    os.remove(os.path.join(self.cache_dir, file))

# Create a singleton instance
translation_cache = TranslationCache() 