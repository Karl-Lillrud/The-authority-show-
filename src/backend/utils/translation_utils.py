import os
import openai
from typing import Dict, Optional, List
from dotenv import load_dotenv
from .translation_cache import translation_cache
from .content_collector import content_collector

load_dotenv()

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

class TranslationService:
    def __init__(self):
        self.client = openai.OpenAI()
        self.default_model = "gpt-3.5-turbo"
        self.supported_languages = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "ar": "Arabic",
            "hi": "Hindi",
            "tr": "Turkish",
            "nl": "Dutch",
            "pl": "Polish",
            "sv": "Swedish",
            "da": "Danish",
            "fi": "Finnish",
            "no": "Norwegian",
            "cs": "Czech",
            "hu": "Hungarian",
            "el": "Greek",
            "he": "Hebrew",
            "id": "Indonesian",
            "ms": "Malay",
            "th": "Thai",
            "vi": "Vietnamese"
        }
        # Map browser language codes to our supported languages
        self.language_mapping = {
            "en-US": "en",
            "en-GB": "en",
            "es-ES": "es",
            "es-MX": "es",
            "fr-FR": "fr",
            "fr-CA": "fr",
            "de-DE": "de",
            "it-IT": "it",
            "pt-BR": "pt",
            "pt-PT": "pt",
            "ru-RU": "ru",
            "zh-CN": "zh",
            "zh-TW": "zh",
            "ja-JP": "ja",
            "ko-KR": "ko"
        }

    def detect_browser_language(self, accept_language: str) -> str:
        """
        Detect the user's preferred language from browser's Accept-Language header
        Returns the corresponding language code from our supported languages
        """
        if not accept_language:
            return "en"  # Default to English if no language header

        # Parse the Accept-Language header
        languages = [lang.strip().split(';')[0] for lang in accept_language.split(',')]
        
        # Try to find a match in our language mapping
        for lang in languages:
            if lang in self.language_mapping:
                return self.language_mapping[lang]
            # Try without the region code
            base_lang = lang.split('-')[0]
            if base_lang in self.supported_languages:
                return base_lang
        
        return "en"  # Default to English if no match found

    def translate_text(self, text: str, target_language: str, source_language: Optional[str] = None) -> Dict:
        """
        Translate text to target language using OpenAI's API
        """
        if not text:
            return {"error": "No text provided for translation"}

        if target_language not in self.supported_languages:
            return {"error": f"Unsupported target language: {target_language}"}

        try:
            prompt = f"Translate the following text to {self.supported_languages[target_language]}"
            if source_language:
                prompt += f" from {self.supported_languages[source_language]}"
            prompt += f":\n\n{text}"

            response = self.client.chat.completions.create(
                model=self.default_model,
                messages=[
                    {"role": "system", "content": "You are a professional translator. Provide only the translated text without any additional explanations or notes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )

            translated_text = response.choices[0].message.content.strip()
            
            return {
                "translated_text": translated_text,
                "source_language": source_language,
                "target_language": target_language
            }

        except Exception as e:
            return {"error": f"Translation failed: {str(e)}"}

    def translate_app_content(self, content: Dict[str, str], target_language: str) -> Dict[str, str]:
        """
        Translate all app content to target language
        """
        if not content:
            return {"error": "No content provided for translation"}

        if target_language not in self.supported_languages:
            return {"error": f"Unsupported target language: {target_language}"}

        # Check cache first
        cached_translations = translation_cache.get_cached_translations(target_language)
        if cached_translations:
            # Only translate new content
            new_content = {k: v for k, v in content.items() if k not in cached_translations}
            if not new_content:
                return cached_translations

            # Translate new content
            try:
                translated_new = self._translate_content_batch(new_content, target_language)
                # Merge with cached translations
                cached_translations.update(translated_new)
                # Update cache
                translation_cache.cache_translations(target_language, cached_translations)
                return cached_translations
            except Exception as e:
                return {"error": f"Translation failed: {str(e)}"}

        # No cache, translate everything
        try:
            translated_content = self._translate_content_batch(content, target_language)
            # Cache the translations
            translation_cache.cache_translations(target_language, translated_content)
            return translated_content
        except Exception as e:
            return {"error": f"Translation failed: {str(e)}"}

    def _translate_content_batch(self, content: Dict[str, str], target_language: str) -> Dict[str, str]:
        """
        Translate a batch of content
        """
        # Prepare the content for batch translation
        content_items = [f"{key}: {value}" for key, value in content.items()]
        content_text = "\n".join(content_items)

        prompt = f"""Translate the following app content to {self.supported_languages[target_language]}.
        Maintain the same keys and only translate the values.
        Format: key: translated_value
        
        Content:
        {content_text}"""

        response = self.client.chat.completions.create(
            model=self.default_model,
            messages=[
                {"role": "system", "content": "You are a professional translator. Translate only the values after the colons, keeping the keys unchanged."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        translated_text = response.choices[0].message.content.strip()
        
        # Parse the translated content back into a dictionary
        translated_content = {}
        for line in translated_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                translated_content[key.strip()] = value.strip()

        return translated_content

    def get_supported_languages(self) -> Dict:
        """
        Return list of supported languages
        """
        return self.supported_languages

    def collect_and_translate(self, target_language: str) -> Dict[str, str]:
        """
        Collect all app content and translate it to target language
        """
        # Collect all content
        content = content_collector.collect_content()
        
        # Translate the content
        return self.translate_app_content(content, target_language)

# Create a singleton instance
translation_service = TranslationService() 