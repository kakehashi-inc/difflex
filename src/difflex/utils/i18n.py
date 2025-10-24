"""Internationalization (i18n) support using JSON translation files."""

import json
import locale
from pathlib import Path
from typing import Dict, Optional

# Singleton translator instance
_translator: Optional['Translator'] = None


class Translator:
    """Translator class for loading and managing translations."""

    def __init__(self, language: Optional[str] = None):
        """
        Initialize translator.

        Args:
            language: Language code (e.g., 'ja-JP', 'en-US').
                     If None, auto-detect from system locale.
        """
        self.locales_dir = Path(__file__).parent.parent / "locales"
        self.translations: Dict[str, str] = {}
        self.current_language = language or self._detect_system_language()
        self._load_translations()

    def _detect_system_language(self) -> str:
        """
        Detect system language.

        Returns:
            Language code (e.g., 'ja-JP', 'en-US')
        """
        try:
            # Get system locale
            sys_locale = locale.getlocale()[0]
            if sys_locale:
                # Convert Python locale to our format
                if sys_locale.startswith('ja') or 'Japanese' in sys_locale:
                    return 'ja-JP'
                elif sys_locale.startswith('en') or 'English' in sys_locale:
                    return 'en-US'
        except Exception:
            pass
        
        # Default to English
        return 'en-US'

    def _load_translations(self):
        """Load translations from JSON file."""
        # Try to load the specified language
        lang_file = self.locales_dir / f"{self.current_language}.json"
        
        if not lang_file.exists():
            # Fallback to English
            self.current_language = 'en-US'
            lang_file = self.locales_dir / "en-US.json"
        
        if lang_file.exists():
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
            except Exception as e:
                print(f"Failed to load translations: {e}")
                self.translations = {}
        else:
            print(f"Translation file not found: {lang_file}")
            self.translations = {}

    def set_language(self, language: str):
        """
        Change current language.

        Args:
            language: Language code (e.g., 'ja-JP', 'en-US')
        """
        self.current_language = language
        self._load_translations()

    def translate(self, key: str, *args, **kwargs) -> str:
        """
        Translate a key to the current language.

        Args:
            key: Translation key
            *args: Positional arguments for string formatting
            **kwargs: Keyword arguments for string formatting

        Returns:
            Translated string
        """
        text = self.translations.get(key, key)
        
        # Apply formatting if arguments provided
        if args or kwargs:
            try:
                return text.format(*args, **kwargs)
            except (KeyError, IndexError, ValueError):
                return text
        
        return text

    def get_available_languages(self) -> Dict[str, str]:
        """
        Get available languages.

        Returns:
            Dictionary of language code to display name
        """
        languages = {}
        
        if self.locales_dir.exists():
            for lang_file in self.locales_dir.glob("*.json"):
                lang_code = lang_file.stem
                
                # Load language name from the file
                try:
                    with open(lang_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Use the language's own name if available
                        if lang_code == 'ja-JP':
                            lang_name = data.get('language_ja', '日本語')
                        elif lang_code == 'en-US':
                            lang_name = data.get('language_en', 'English')
                        else:
                            lang_name = lang_code
                        
                        languages[lang_code] = lang_name
                except Exception:
                    languages[lang_code] = lang_code
        
        return languages


def init_translator(language: Optional[str] = None) -> Translator:
    """
    Initialize the global translator instance.

    Args:
        language: Language code. If None, auto-detect.

    Returns:
        Translator instance
    """
    global _translator
    _translator = Translator(language)
    return _translator


def get_translator() -> Translator:
    """
    Get the global translator instance.

    Returns:
        Translator instance
    """
    global _translator
    if _translator is None:
        _translator = Translator()
    return _translator


def tr(key: str, *args, **kwargs) -> str:
    """
    Translate a key (convenience function).

    Args:
        key: Translation key
        *args: Positional arguments for string formatting
        **kwargs: Keyword arguments for string formatting

    Returns:
        Translated string
    """
    return get_translator().translate(key, *args, **kwargs)


def set_language(language: str):
    """
    Change current language.

    Args:
        language: Language code (e.g., 'ja-JP', 'en-US')
    """
    get_translator().set_language(language)
