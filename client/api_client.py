import requests
import json

class APIClient:
    def __init__(self, base_url="http://localhost:8000", api_key=None):
        self.base_url = base_url
        # Use provided key, or env var, or default dev key
        import os
        self.api_key = api_key or os.getenv("ELIZA_API_KEY", "eliza-client-key-12345")

    def _get_headers(self):
        return {"X-API-Key": self.api_key}

    def check_connection(self):
        try:
            response = requests.get(f"{self.base_url}/api/v1/system/status", timeout=2)
            return response.status_code == 200
        except Exception as e:
            print(f"Connection check failed: {e}")
            return False

    def get_status(self):
        retries = 3
        timeout = 5
        last_error = None
        
        for attempt in range(retries):
            try:
                response = requests.get(f"{self.base_url}/api/v1/system/status", timeout=timeout, headers=self._get_headers())
                if response.status_code == 200:
                    return response.json()
                return {"error": response.status_code}
            except Exception as e:
                last_error = e
                continue
                
        return {"error": str(last_error)}

    def send_message(self, message: str, use_search: bool = False, force_search: bool = False):
        try:
            # Server logic prioritizes force_search, so we map use_search to it to ensure user intent is respected
            if use_search:
                force_search = True
                
            payload = {
                "message": message,
                "use_search": use_search,
                "force_search": force_search
            }
            response = requests.post(f"{self.base_url}/api/v1/chat/chat", json=payload, headers=self._get_headers(), timeout=30)
            if response.status_code == 200:
                return response.json()
            return {"response": f"Error: {response.status_code} - {response.text}", "search_used": False}
        except requests.exceptions.Timeout:
            return {"response": "Error: Connection timed out. Please check your network.", "search_used": False}
        except requests.exceptions.ConnectionError:
             return {"response": "Error: Could not connect to server. Is it running?", "search_used": False}
        except Exception as e:
            return {"response": f"Connection Error: {str(e)}", "search_used": False}

    def clear_memory(self):
        try:
            requests.delete(f"{self.base_url}/api/v1/profile/memory", headers=self._get_headers())
            return True
        except Exception as e:
            print(f"Error clearing memory: {e}")
            return False

    def get_config(self):
        try:
            response = requests.get(f"{self.base_url}/api/v1/config/", headers=self._get_headers())
            return response.json()
        except Exception as e:
            print(f"Error getting config: {e}")
            return {}

    def update_config(self, config):
        try:
            requests.post(f"{self.base_url}/api/v1/config/", json=config, headers=self._get_headers())
            return True
        except Exception as e:
            print(f"Error updating config: {e}")
            return False

    def get_voices(self):
        try:
            response = requests.get(f"{self.base_url}/api/v1/audio/voices", headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            print(f"Error getting voices: {e}")
            return {}

    def get_tts(self, text, speed=1.0, volume=1.0, voice_id="default"):
        try:
            payload = {
                "text": text,
                "speed": speed,
                "volume": volume,
                "voice_id": voice_id
            }
            response = requests.post(f"{self.base_url}/api/v1/audio/tts", json=payload, stream=True, headers=self._get_headers())
            if response.status_code == 200:
                return response.content
            return None
        except:
            return None

    def get_profile(self):
        try:
            response = requests.get(f"{self.base_url}/api/v1/profile/", headers=self._get_headers())
            return response.json()
        except:
            return {}

    def update_profile(self, profile):
        try:
            requests.post(f"{self.base_url}/api/v1/profile/", json=profile, headers=self._get_headers())
            return True
        except:
            return False

    def export_profile(self):
        try:
            response = requests.get(f"{self.base_url}/api/v1/profile/export", headers=self._get_headers())
            if response.status_code == 200:
                return response.json().get("json")
            return None
        except:
            return None

    def import_profile(self, profile_data):
        try:
            response = requests.post(f"{self.base_url}/api/v1/profile/import", json={"profile": profile_data}, headers=self._get_headers())
            return response.status_code == 200
        except:
            return False

    def transcribe_audio(self, file_path):
        try:
            with open(file_path, "rb") as f:
                files = {"file": f}
                response = requests.post(f"{self.base_url}/api/v1/audio/transcribe", files=files, headers=self._get_headers())
            if response.status_code == 200:
                return response.json().get("text", "")
            return f"Error: {response.status_code}"
        except Exception as e:
            return f"Error: {e}"

    # --- Prompt Management ---

    def get_prompts(self):
        try:
            response = requests.get(f"{self.base_url}/api/v1/config/prompts", headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Error getting prompts: {e}")
            return []
        
    def save_prompt(self, prompt_data):
        try:
            response = requests.post(f"{self.base_url}/api/v1/config/prompts", json=prompt_data, headers=self._get_headers())
            return response.status_code == 200
        except Exception as e:
            print(f"Error saving prompt: {e}")
            return False

    def create_project(self, name: str, template: str = ""):
        try:
            payload = {"name": name, "template": template}
            response = requests.post(f"{self.base_url}/api/v1/projects/", json=payload, headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            return {"error": response.text}
        except Exception as e:
            return {"error": str(e)}

    def delete_project(self, project_id: str):
        try:
            response = requests.delete(f"{self.base_url}/api/v1/projects/{project_id}", headers=self._get_headers())
            return response.status_code == 200
        except Exception as e:
            print(f"Delete error: {e}")
            return False

    def list_output_files(self):
        try:
            response = requests.get(f"{self.base_url}/api/v1/files/output", headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            return {"files": []}
        except Exception as e:
            return {"error": str(e), "files": []}

    def list_projects(self):
        try:
            response = requests.get(f"{self.base_url}/api/v1/projects/", headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            return {"error": response.text}
        except Exception as e:
            return {"error": str(e)}

    def list_models(self, q: str = ""):
        try:
            params = {"q": q} if q else None
            response = requests.get(f"{self.base_url}/api/v1/models/", params=params, headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            return {"error": response.text}
        except Exception as e:
            return {"error": str(e)}

    def create_agent(self, project_id: str, role_name: str, model_name: str, description: str = ""):
        try:
            payload = {"role_name": role_name, "model_name": model_name, "description": description}
            response = requests.post(f"{self.base_url}/api/v1/projects/{project_id}/agents", json=payload, headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            return {"error": response.text}
        except Exception as e:
            return {"error": str(e)}

    def list_agents(self, project_id: str):
        try:
            response = requests.get(f"{self.base_url}/api/v1/projects/{project_id}/agents", headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            return {"error": response.text}
        except Exception as e:
            return {"error": str(e)}

    def get_project_log(self, project_id: str):
        try:
            response = requests.get(f"{self.base_url}/api/v1/projects/{project_id}/log", headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            return {"error": response.text}
        except Exception as e:
            return {"error": str(e)}

    def orchestrate(self, project_id: str, message: str):
        try:
            payload = {"message": message}
            response = requests.post(f"{self.base_url}/api/v1/projects/{project_id}/orchestrate", json=payload, headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            return {"error": response.text}
        except Exception as e:
            return {"error": str(e)}

    def control_workflow(self, project_id: str, action: str, message: str = ""):
        try:
            payload = {"action": action, "message": message}
            response = requests.post(f"{self.base_url}/api/v1/projects/{project_id}/control", json=payload, headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            return {"error": response.text}
        except Exception as e:
            return {"error": str(e)}

    def init_team(self, project_id: str):
        try:
            response = requests.post(f"{self.base_url}/api/v1/projects/{project_id}/init_team", json={}, headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            return {"error": response.text}
        except Exception as e:
            return {"error": str(e)}

    def delete_prompt(self, template_id):
        return False

    def get_active_prompt_id(self):
        return None

    def set_active_prompt(self, template_id):
        return False
