import json
import os
from PyQt5.QtCore import QObject, pyqtSignal, QSettings

class I18nManager(QObject):
    language_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        settings = QSettings("Eliza", "Client")
        self.current_lang = settings.value("general/language", "zh")
        self.translations = {}
        self.load_translations()

    def load_translations(self):
        base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "locales")
        for filename in os.listdir(base_path):
            if filename.endswith(".json"):
                lang_code = filename.split(".")[0]
                try:
                    with open(os.path.join(base_path, filename), "r", encoding="utf-8") as f:
                        self.translations[lang_code] = json.load(f)
                except Exception as e:
                    print(f"Error loading translation {filename}: {e}")

    def set_language(self, lang_code):
        if lang_code in self.translations and lang_code != self.current_lang:
            self.current_lang = lang_code
            self.language_changed.emit(lang_code)

    def t(self, key, *args):
        lang_data = self.translations.get(self.current_lang, {})
        text = lang_data.get(key, key)
        if args:
            try:
                return text.format(*args)
            except IndexError:
                return text
        return text

I18N = I18nManager()
