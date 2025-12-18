from PyQt5.QtCore import QObject, pyqtSignal

class StateSignals(QObject):
    changed = pyqtSignal(str, object) # key, new_value

class Store(QObject):
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Store, cls).__new__(cls)
            cls._instance.signals = StateSignals()
            cls._instance._state = {
                "user": None,
                "status": "offline",
                "layout": "default",
                "chat_history": [],
                "voices": [],
                "tts_config": {},
                "is_processing": False
            }
        return cls._instance

    def get(self, key, default=None):
        return self._state.get(key, default)

    def set(self, key, value):
        if self._state.get(key) != value:
            self._state[key] = value
            self.signals.changed.emit(key, value)

    def update(self, data):
        for k, v in data.items():
            self.set(k, v)

STORE = Store()
