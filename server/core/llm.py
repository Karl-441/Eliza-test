import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

from .config import settings
from .memory import memory_manager

import datetime

class LLMEngine:
    def __init__(self):
        self.model = None
        self.loaded_at = None
        self.status = "initializing" # initializing, ready, error
        self.last_error = None
        self.load_model()

    def load_model(self):
        self.model = None
        self.loaded_at = None
        self.status = "loading"
        self.last_error = None
        
        if not Llama:
            self.status = "error"
            self.last_error = "llama-cpp-python not installed"
            logger.warning("llama-cpp-python not installed. LLM will not work.")
            return

        if not os.path.exists(settings.model_path):
            self.status = "error"
            self.last_error = f"Model not found at {settings.model_path}"
            logger.warning(f"Model not found at {settings.model_path}. Please download a GGUF model.")
            return

        try:
            self.model = Llama(
                model_path=settings.model_path,
                n_ctx=settings.n_ctx,
                n_threads=settings.n_threads,
                verbose=False
            )
            self.loaded_at = datetime.datetime.now().isoformat()
            self.status = "ready"
            logger.info(f"Model loaded from {settings.model_path}")
        except Exception as e:
            self.status = "error"
            self.last_error = str(e)
            logger.error(f"Error loading model: {e}")

    def reload_model(self):
        logger.info("Reloading model...")
        self.load_model()

    def generate_response(self, user_input: str, system_prompt: str = None) -> str:
        if not self.model:
            return f"System Alert: Neural Cloud Model not found or failed to load.\nPath: {settings.model_path}\nPlease configure the model path in SETTINGS."

        if not system_prompt:
            system_prompt = memory_manager.get_context_prompt()

        # Prepare messages including history
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(memory_manager.get_history())
        messages.append({"role": "user", "content": user_input})
        
        logger.info(f"Generating response for input length: {len(user_input)}")

        try:
            # Set max_tokens explicitly to avoid default truncation
            # Using 0 or -1 usually means infinite in some libs, but for llama-cpp-python, 
            # safe bet is to let it default or set high. 
            # We will use settings.n_ctx if possible, but create_chat_completion 
            # handles context window automatically. 
            # However, to prevent "9 char" issue, we explicitly request a large generation window.
            
            response = self.model.create_chat_completion(
                messages=messages,
                temperature=settings.temperature,
                top_p=settings.top_p,
                max_tokens=2048, # Explicitly set high max_tokens
                stream=False
            )
            
            content = response["choices"][0]["message"]["content"]
            finish_reason = response["choices"][0]["finish_reason"]
            
            logger.info(f"Response generated. Length: {len(content)}. Finish reason: {finish_reason}")
            
            if len(content) <= 9:
                logger.warning(f"Short response detected: '{content}'")
                
            return content
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error generating response: {e}"

    def stream_response(self, user_input: str, system_prompt: str = None):
        if not self.model:
            yield "Error: LLM model is not loaded."
            return

        if not system_prompt:
            system_prompt = memory_manager.get_context_prompt()

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(memory_manager.get_history())
        messages.append({"role": "user", "content": user_input})

        try:
            stream = self.model.create_chat_completion(
                messages=messages,
                temperature=settings.temperature,
                top_p=settings.top_p,
                stream=True
            )
            for chunk in stream:
                if "content" in chunk["choices"][0]["delta"]:
                    yield chunk["choices"][0]["delta"]["content"]
        except Exception as e:
            yield f"Error: {e}"

llm_engine = LLMEngine()
