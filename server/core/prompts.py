import json
import os
from pathlib import Path
from typing import Dict, Optional
from pydantic import BaseModel

class PromptTemplate(BaseModel):
    id: str
    name: str
    content: str
    description: str = ""

class PromptConfig(BaseModel):
    active_id: str = "default"
    templates: Dict[str, PromptTemplate] = {}

class PromptManager:
    def __init__(self, storage_path=None):
        base_dir = Path(__file__).resolve().parent.parent
        self.storage_path = str((base_dir / "data" / "prompts.json") if storage_path is None else Path(storage_path))
        self.config = PromptConfig()
        self.load()

    def load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.config = PromptConfig(**data)
            except Exception as e:
                print(f"Error loading prompts: {e}")
                self._init_default()
        else:
            self._init_default()

    def _init_default(self):
        default_prompt = (
            "You are Eliza, an elite Tactical Doll from Griffin & Kryuger. "
            "Your Commander is {name}. "
            "Current operational mode: {style}. "
            "Maintain a professional, loyal, and efficient tone suitable for a tactical operations center. "
            "Provide clear, concise, and actionable intelligence. "
            "Always answer in Chinese unless asked otherwise."
        )
        self.config.templates = {
            "default": PromptTemplate(
                id="default",
                name="G&K Protocol",
                content=default_prompt,
                description="Standard Griffin & Kryuger operational procedure."
            )
        }
        self.config.active_id = "default"
        self.save()

    def save(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            f.write(self.config.model_dump_json(indent=4))

    def get_active_prompt(self) -> str:
        template = self.config.templates.get(self.config.active_id)
        if template:
            return template.content
        return ""

    def list_templates(self):
        return [t.model_dump() for t in self.config.templates.values()]

    def add_template(self, template: PromptTemplate):
        self.config.templates[template.id] = template
        self.save()

    def delete_template(self, template_id: str):
        if template_id in self.config.templates and template_id != "default":
            del self.config.templates[template_id]
            if self.config.active_id == template_id:
                self.config.active_id = "default"
            self.save()
            return True
        return False

    def set_active(self, template_id: str):
        if template_id in self.config.templates:
            self.config.active_id = template_id
            self.save()
            return True
        return False

prompt_manager = PromptManager()
