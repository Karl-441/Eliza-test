import os
import glob
import logging
import json
import threading
import requests
import time
import subprocess
from typing import List, Dict, Optional
from pathlib import Path
from .config import settings
from .llm import llm_engine

logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self):
        self.models_dir = settings.models_root_dir
        self.download_tasks = {} # id -> {status, progress, error, filename}
        self.config_path = Path(__file__).resolve().parent.parent / "model_config.json"

    def list_models(self) -> List[Dict[str, str]]:
        # Update dir from settings in case it changed
        self.models_dir = settings.models_root_dir
        if not os.path.exists(self.models_dir):
            return []
        
        # Look for .gguf files recursively or just top level? 
        # User said "sync download location to model root directory"
        # huggingface-cli usually creates subdirs if repo structure is kept, 
        # but with single file download it might be flat or in subdir.
        # We'll search recursively for now to find models in subfolders.
        files = []
        for root, dirs, filenames in os.walk(self.models_dir):
            for filename in filenames:
                if filename.endswith(".gguf"):
                    files.append(os.path.join(root, filename))
                    
        models = []
        for f in files:
            models.append({
                "name": os.path.basename(f),
                "path": f,
                "size_mb": round(os.path.getsize(f) / (1024*1024), 2),
                "status": "ready"
            })
        return models

    def get_remote_models(self) -> List[Dict]:
        """List models from model_config.json"""
        if not self.config_path.exists():
            return []
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("models", [])
        except Exception as e:
            logger.error(f"Failed to load model config: {e}")
            return []

    def load_model(self, model_name: str) -> bool:
        # We need to find the full path since list_models returns basename as name
        # but now models can be in subdirs.
        # If model_name is absolute, verify. If relative/basename, find it.
        
        target_path = None
        if os.path.isabs(model_name):
            target_path = model_name
        else:
            # Search for it
            self.models_dir = settings.models_root_dir
            for root, dirs, filenames in os.walk(self.models_dir):
                if model_name in filenames:
                    target_path = os.path.join(root, model_name)
                    break
        
        if not target_path or not os.path.exists(target_path):
            logger.error(f"Model not found: {model_name}")
            return False

        # Security check: ensure path is within models_dir
        # Allow if it is in the configured root
        try:
            abs_root = os.path.abspath(self.models_dir)
            abs_target = os.path.abspath(target_path)
            if not abs_target.startswith(abs_root):
                 logger.error(f"Invalid model path (outside root): {target_path}")
                 return False
        except:
             pass

        # Update settings
        settings.model_path = target_path
        settings.save()
        
        # Trigger reload
        try:
            llm_engine.reload_model()
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def start_download(self, url_or_repo: str, filename: str) -> str:
        """Start a background download task using huggingface-cli if possible"""
        task_id = f"dl_{int(time.time())}_{filename}"
        self.download_tasks[task_id] = {
            "status": "pending",
            "progress": 0,
            "filename": filename,
            "url": url_or_repo,
            "error": None
        }
        
        thread = threading.Thread(target=self._download_worker, args=(task_id, url_or_repo, filename))
        thread.daemon = True
        thread.start()
        
        return task_id

    def _download_worker(self, task_id: str, url_or_repo: str, filename: str):
        # Ensure latest settings are used
        self.models_dir = settings.models_root_dir
        os.makedirs(self.models_dir, exist_ok=True)
        
        self.download_tasks[task_id]["status"] = "downloading"
        
        # Check if it looks like a HF Repo ID or URL
        repo_id = url_or_repo
        specific_file = filename
        
        is_hf_url = "huggingface.co" in url_or_repo
        
        if is_hf_url:
            # Pattern: huggingface.co/<org>/<model>/resolve/<branch>/<filename>
            parts = url_or_repo.split("huggingface.co/")
            if len(parts) > 1:
                # Remove query params if any
                path = parts[1].split("?")[0]
                path_parts = path.split("/")
                if len(path_parts) >= 2:
                    repo_id = f"{path_parts[0]}/{path_parts[1]}"
                    # If user didn't provide specific filename, try to guess or use passed one
                    if len(path_parts) > 4 and path_parts[2] == "resolve":
                        # e.g. resolve/main/file.gguf
                        specific_file = "/".join(path_parts[4:])
                    elif len(path_parts) > 3 and path_parts[2] == "blob":
                        specific_file = "/".join(path_parts[4:])
                        
        if not specific_file:
             specific_file = filename

        # Heuristic: if repo_id contains slashes and no http, it's likely a repo ID
        is_repo_id = "/" in repo_id and "http" not in repo_id

        # Use CLI if it's a repo ID or we extracted one
        if is_repo_id:
             self._download_via_cli(task_id, repo_id, specific_file)
        else:
             # Fallback to requests
             logger.info(f"Not a HF repo ID, using direct download: {url_or_repo}")
             self._download_via_requests(task_id, url_or_repo, specific_file)

    def _download_via_cli(self, task_id, repo_id, filename):
        try:
            env = os.environ.copy()
            if "HF_ENDPOINT" not in env:
                env["HF_ENDPOINT"] = "https://hf-mirror.com"
            
            # Construct Command
            # huggingface-cli download <repo_id> <filename> --local-dir <dir> --local-dir-use-symlinks False
            cmd = [
                "huggingface-cli", "download",
                repo_id,
                filename,
                "--local-dir", self.models_dir,
                "--local-dir-use-symlinks", "False",
                "--resume-download"
            ]
            
            logger.info(f"Running HF CLI: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                env=env
            )
            
            # We can't easily parse progress from CLI in real-time without complex logic as it uses stderr/tqdm
            # We'll just wait for it. 
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                self.download_tasks[task_id]["status"] = "completed"
                self.download_tasks[task_id]["progress"] = 100
                logger.info(f"Download completed: {filename}")
            else:
                 raise Exception(f"CLI failed: {stderr}")

        except Exception as e:
            logger.error(f"CLI Download failed: {e}")
            self.download_tasks[task_id]["status"] = "error"
            self.download_tasks[task_id]["error"] = str(e)

    def _download_via_requests(self, task_id, url, filename):
        target_path = os.path.join(self.models_dir, filename)
        temp_path = target_path + ".download"
        
        try:
            headers = {}
            mode = 'wb'
            downloaded = 0
            
            if os.path.exists(temp_path):
                downloaded = os.path.getsize(temp_path)
                headers['Range'] = f'bytes={downloaded}-'
                mode = 'ab'
                logger.info(f"Resuming download for {filename} from {downloaded} bytes")

            response = requests.get(url, stream=True, headers=headers, timeout=30)
            
            # Check if server supports range
            if response.status_code == 416: # Range Not Satisfiable (likely complete)
                logger.warning(f"Range not satisfiable for {filename}, checking if complete.")
                # We can't verify easily without total size, but let's assume if it happened, we might be done or error.
                # Ideally we check Content-Range or similar.
                # For now, if we get 416, we might want to restart or assume done.
                # Let's assume done if we have some bytes.
                if downloaded > 0:
                    os.rename(temp_path, target_path)
                    self.download_tasks[task_id]["status"] = "completed"
                    self.download_tasks[task_id]["progress"] = 100
                    return
            
            if response.status_code not in [200, 206]:
                raise Exception(f"HTTP {response.status_code}: {response.reason}")
                
            if response.status_code == 200:
                # Server ignored Range, full download
                downloaded = 0
                mode = 'wb'
                logger.info(f"Server does not support resume, restarting download for {filename}")

            total_size = int(response.headers.get('content-length', 0))
            if response.status_code == 206:
                # Content-Length is the REMAINING size
                total_size += downloaded
            
            with open(temp_path, mode) as f:
                for data in response.iter_content(chunk_size=8192):
                    f.write(data)
                    downloaded += len(data)
                    if total_size > 0:
                        progress = int((downloaded / total_size) * 100)
                        self.download_tasks[task_id]["progress"] = progress
            
            # Rename temp to target upon completion
            if os.path.exists(target_path):
                os.remove(target_path)
            os.rename(temp_path, target_path)
            
            self.download_tasks[task_id]["status"] = "completed"
            self.download_tasks[task_id]["progress"] = 100
            
        except Exception as e:
            self.download_tasks[task_id]["status"] = "error"
            self.download_tasks[task_id]["error"] = str(e)
            logger.error(f"Download failed for {filename}: {e}")

    def get_download_status(self, task_id: str):
        return self.download_tasks.get(task_id)
    
    def get_all_downloads(self):
        return self.download_tasks

model_manager = ModelManager()
