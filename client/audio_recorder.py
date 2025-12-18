from PyQt5.QtCore import QObject, pyqtSignal
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import queue
import tempfile
import os
import time

class AudioRecorder(QObject):
    # Signals
    level_changed = pyqtSignal(float)  # Emits RMS value (0.0 - 1.0 approx)
    silence_detected = pyqtSignal()    # Emits when VAD detects silence
    
    def __init__(self):
        super().__init__()
        self.recording = False
        self.audio_queue = queue.Queue()
        self.stream = None
        self.samplerate = 16000
        self.channels = 1
        
        # VAD Settings
        self.vad_enabled = False
        self.vad_threshold = 0.01  # RMS threshold
        self.vad_silence_timeout = 1.5  # Seconds of silence to trigger stop
        
        # VAD State
        self.last_speech_time = 0
        self.speech_detected = False

    def set_vad_parameters(self, enabled: bool, threshold: float, timeout: float):
        self.vad_enabled = enabled
        self.vad_threshold = threshold
        self.vad_silence_timeout = timeout

    def start_recording(self):
        if self.recording:
            return
            
        self.recording = True
        self.audio_queue = queue.Queue()
        self.speech_detected = False
        self.last_speech_time = time.time()
        
        def callback(indata, frames, time_info, status):
            if status:
                print(status)
            self.audio_queue.put(indata.copy())
            
            # Calculate Level (RMS)
            # indata is float32 by default with sounddevice
            rms = float(np.sqrt(np.mean(indata**2)))
            self.level_changed.emit(rms)
            
            # VAD Logic
            if self.vad_enabled:
                current_time = time.time()
                if rms > self.vad_threshold:
                    self.last_speech_time = current_time
                    self.speech_detected = True
                else:
                    # Only trigger if we have detected speech previously
                    if self.speech_detected and (current_time - self.last_speech_time > self.vad_silence_timeout):
                        self.silence_detected.emit()
                        # We emit the signal, but let the controller decide to stop
                        # to avoid threading issues if we stop here directly (though stream.stop is thread-safe usually)

        try:
            self.stream = sd.InputStream(samplerate=self.samplerate, 
                                         channels=self.channels, 
                                         callback=callback)
            self.stream.start()
        except Exception as e:
            print(f"Error starting recording: {e}")
            self.recording = False

    def stop_recording(self) -> str:
        if not self.recording:
            return None
            
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        # Collect data
        data = []
        while not self.audio_queue.empty():
            data.append(self.audio_queue.get())
            
        if not data:
            return None
            
        audio_data = np.concatenate(data, axis=0)
        
        # Save to temp file
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        
        # Scipy wavfile write
        # sounddevice returns float32, we can save as float32 wav or convert to int16
        # standard wav is usually int16, but float32 is supported. 
        # For compatibility, let's keep it as is (float32 usually works with faster-whisper)
        wav.write(path, self.samplerate, audio_data)
        return path
