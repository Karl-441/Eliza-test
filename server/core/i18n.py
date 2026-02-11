import json
import os
from pathlib import Path
from server.core.config import settings

class I18nManager:
    def __init__(self):
        self.translations = {}
        self.load_translations()

    def load_translations(self):
        base_path = Path(__file__).parent.parent / "locales"
        if not base_path.exists():
            return
            
        for file_path in base_path.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lang_code = file_path.stem
                    self.translations[lang_code] = json.load(f)
            except Exception as e:
                print(f"Error loading translation {file_path}: {e}")

    def t(self, key, *args, lang=None):
        if lang is None:
            lang = getattr(settings, "language", "zh")
            
        lang_data = self.translations.get(lang, {})
        # Fallback to English if key not found in target language
        if key not in lang_data and lang != "en":
             lang_data = self.translations.get("en", {})
             
        text = lang_data.get(key, key)
        
        if args:
            try:
                return text.format(*args)
            except IndexError:
                return text
        return text

I18N = I18nManager()
