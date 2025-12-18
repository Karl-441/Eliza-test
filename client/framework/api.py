from PyQt5.QtCore import QThread, pyqtSignal, QObject
from ..api_client import APIClient
from .state import STORE

class ApiWorker(QThread):
    finished = pyqtSignal(object)
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        
    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({"error": str(e)})

class APIGateway(QObject):
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(APIGateway, cls).__new__(cls)
            cls._instance.client = APIClient()
            cls._instance._cache = {}
        return cls._instance

    def request(self, method_name, *args, **kwargs):
        """Async request wrapper"""
        method = getattr(self.client, method_name, None)
        if not method:
            raise AttributeError(f"APIClient has no method {method_name}")
            
        worker = ApiWorker(method, *args, **kwargs)
        # Caller needs to connect to worker.finished
        return worker

    def get_cached(self, key):
        return self._cache.get(key)

    def set_cache(self, key, value):
        self._cache[key] = value

API = APIGateway()
