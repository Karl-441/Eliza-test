from PyQt5.QtCore import QObject, pyqtSignal, QUrl
from PyQt5.QtWebSockets import QWebSocket
import json

class WebSocketClient(QObject):
    message_received = pyqtSignal(dict)
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.ws = QWebSocket()
        self.ws.connected.connect(self.on_connected)
        self.ws.disconnected.connect(self.on_disconnected)
        self.ws.textMessageReceived.connect(self.on_message)
        
    def start(self):
        self.ws.open(QUrl(self.url))
        
    def stop(self):
        self.ws.close()
        
    def on_connected(self):
        print("WS Connected")
        self.connected.emit()
        
    def on_disconnected(self):
        print("WS Disconnected")
        self.disconnected.emit()
        
    def on_message(self, message):
        try:
            data = json.loads(message)
            self.message_received.emit(data)
        except Exception as e:
            print(f"WS JSON Error: {e}")

    def send_json(self, data):
        if self.ws.isValid():
            self.ws.sendTextMessage(json.dumps(data))
