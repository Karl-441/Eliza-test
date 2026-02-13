import sounddevice as sd
import numpy as np
import queue
import threading
import time
import json
import logging
from PyQt5.QtCore import QObject, pyqtSignal
import websocket
import ssl

logger = logging.getLogger(__name__)

class VoiceSystem(QObject):
    # Signals
    level_changed = pyqtSignal(float)
    wake_detected = pyqtSignal()
    text_received = pyqtSignal(str, bool) # text, is_final
    status_changed = pyqtSignal(str)
    
    def __init__(self, api_url="ws://127.0.0.1:8000/api/v1/audio/stream"):
        super().__init__()
        self.api_url = api_url
        self.running = False
        self.mode = "wake_word" # wake_word, active, continuous
        self.wake_word = "eliza"
        
        # Audio Config
        self.samplerate = 16000
        self.channels = 1
        self.blocksize = 4096
        
        # VAD Config
        self.vad_enabled = True
        self.vad_threshold = 0.015
        self.vad_timeout = 1.2
        self.last_speech_time = 0
        self.is_speaking = False
        
        # Queues
        self.audio_queue = queue.Queue()
        
        # WebSocket
        self.ws = None
        self.ws_thread = None
        self.connected = False
        
        # Logic State
        self.buffer = []
        self.pending_transcription = False

    def start(self):
        if self.running: return
        self.running = True
        
        # Start Audio Thread
        self.audio_thread = threading.Thread(target=self._audio_loop)
        self.audio_thread.daemon = True
        self.audio_thread.start()
        
        # Start WS Thread
        self.ws_thread = threading.Thread(target=self._ws_loop)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        
        self.status_changed.emit("Voice System Started")

    def stop(self):
        self.running = False
        if self.ws:
            self.ws.close()

    def set_mode(self, mode):
        self.mode = mode
        self.status_changed.emit(f"Mode: {mode}")

    def _audio_loop(self):
        def callback(indata, frames, time, status):
            if status:
                print(status)
            self.audio_queue.put(indata.copy())

        try:
            with sd.InputStream(samplerate=self.samplerate,
                                channels=self.channels,
                                callback=callback,
                                blocksize=self.blocksize):
                while self.running:
                    # Process audio for VAD and Level
                    # We process in main loop or here? 
                    # Sounddevice callback is in a separate thread.
                    # We can just sleep here and let callback fill queue
                    sd.sleep(100)
        except Exception as e:
            logger.error(f"Audio Error: {e}")
            self.status_changed.emit("Audio Error")

    def _ws_loop(self):
        while self.running:
            try:
                self.ws = websocket.WebSocket()
                self.ws.connect(self.api_url)
                self.connected = True
                self.status_changed.emit("Server Connected")
                
                while self.running and self.ws.connected:
                    # 1. Process Audio Queue
                    chunk = self._get_audio_chunk()
                    if chunk is not None:
                        # VAD & Level
                        rms = float(np.sqrt(np.mean(chunk**2)))
                        self.level_changed.emit(rms)
                        
                        if (not self.vad_enabled) or (rms > self.vad_threshold):
                            self.last_speech_time = time.time()
                            if not self.is_speaking:
                                self.is_speaking = True
                                # Speech started
                        else:
                            if self.is_speaking and (time.time() - self.last_speech_time > self.vad_timeout):
                                self.is_speaking = False
                                # Speech ended -> Commit
                                self._commit_buffer()

                        # Logic based on Mode
                        if self.is_speaking or len(self.buffer) > 0:
                            # Send raw bytes to server
                            # Convert float32 to int16 for compatibility
                            pcm_data = (chunk * 32767).astype(np.int16).tobytes()
                            self.ws.send_binary(pcm_data)
                            self.buffer.append(chunk) # Keep track if we need to replay or analyze
                    
                    # 2. Check for messages (Non-blocking receive is tricky with standard websocket-client)
                    # We usually need a select or separate thread for recv.
                    # For simplicity, we'll use a small timeout recv
                    try:
                        self.ws.settimeout(0.01)
                        result = self.ws.recv()
                        self._handle_server_message(result)
                    except websocket.WebSocketTimeoutException:
                        pass
                    except Exception as e:
                        print(f"Recv Error: {e}")
                        break
                        
            except Exception as e:
                self.connected = False
                self.status_changed.emit("Connection Lost")
                time.sleep(2) # Retry delay

    def _get_audio_chunk(self):
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None

    def _commit_buffer(self):
        if self.connected:
            self.ws.send("COMMIT")
            self.buffer = [] # Clear local buffer

    def _handle_server_message(self, message):
        try:
            data = json.loads(message)
            if data["type"] == "transcription":
                text = data["text"].strip()
                if not text: return
                
                logger.info(f"Heard: {text}")
                
                if self.mode == "wake_word":
                    if self.wake_word.lower() in text.lower():
                        self.wake_detected.emit()
                        self.status_changed.emit("Wake Word Detected")
                        # Auto switch to active?
                        # self.mode = "active" 
                else:
                    self.text_received.emit(text, True)
                    
        except Exception as e:
            logger.error(f"Msg Error: {e}")

