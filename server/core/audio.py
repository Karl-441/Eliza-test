import os
import requests
try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

from .config import settings
from .i18n import I18N

class AudioManager:
    def __init__(self):
        self.asr_model = None
        # Lazy load ASR to save memory if not used
        
    def load_asr(self):
        if not self.asr_model and WhisperModel:
            print("Loading ASR Model...")
            try:
                # Use 'tiny' or 'base' for low memory
                self.asr_model = WhisperModel("base", device="cpu", compute_type="int8")
                print("ASR Model Loaded.")
            except Exception as e:
                print(f"Failed to load ASR: {e}")

    def transcribe(self, audio_path: str) -> str:
        self.load_asr()
        if not self.asr_model:
            return I18N.t("asr_not_available")
        
        try:
            segments, _ = self.asr_model.transcribe(audio_path, beam_size=5)
            text = "".join([segment.text for segment in segments])
            return text
        except Exception as e:
            return I18N.t("transcribe_error").format(error=e)

    def check_tts_health(self) -> dict:
        if not settings.enable_audio:
            return {"status": False, "message": I18N.t("audio_disabled")}
        try:
            # Check connectivity to the TTS API
            response = requests.get(settings.tts_api_url, timeout=2)
            if response.status_code in [200, 404, 405]: # 404/405 means server is reachable
                return {"status": True, "message": I18N.t("tts_online")}
            return {"status": False, "message": I18N.t("tts_http_error").format(code=response.status_code)}
        except Exception as e:
            return {"status": False, "message": str(e)}

    def get_voices(self) -> dict:
        return settings.voice_presets

    def text_to_speech(self, text: str, output_path: str, speed: float = 1.0, volume: float = 1.0, voice_id: str = "default", language: str = "zh"):
        # Call external GPT-SoVITS API
        if not settings.enable_audio:
            print("TTS Disabled in settings.")
            return False
            
        try:
            voice_config = settings.voice_presets.get(voice_id)
            if not voice_config:
                 # Fallback to default if specific voice not found
                 voice_config = settings.voice_presets.get("default", {})

            # Use GET request for GPT-SoVITS simple API
            params = {
                "text": text,
                "text_language": language,
                "speed": speed,
                "volume": volume
            }
            
            # Add voice parameters if available
            if voice_config:
                params.update({
                    "ref_audio_path": voice_config.get("ref_audio_path", ""),
                    "prompt_text": voice_config.get("prompt_text", ""),
                    "prompt_language": voice_config.get("prompt_language", "zh"),
                })

            # Adjust the URL if needed based on specific GPT-SoVITS version
            # Using POST might be safer for long text, but keeping GET as per original implementation for now
            # unless length > 200 chars?
            
            import time
            start_time = time.time()
            
            response = requests.get(f"{settings.tts_api_url}", params=params, timeout=30)
            
            duration = (time.time() - start_time) * 1000
            print(f"TTS Request took {duration:.2f}ms")
            
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                return True
            else:
                print(f"TTS API Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"TTS Error: {e}")
        return False

audio_manager = AudioManager()
