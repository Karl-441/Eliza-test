import json
import re
import asyncio
from typing import List, Optional
from server.core.llm import llm_engine
from server.core.i18n import I18N

def get_planning_prompt(message: str) -> str:
    return f"""{I18N.t("planning_prompt_intro")}
{I18N.t("planning_prompt_req").format(message=message)}

{I18N.t("planning_prompt_format")}
[
    {{
        "id": "task_1",
        "title": "{I18N.t("task_1_title")}",
        "content": "{I18N.t("task_1_content").format(message="...")}",
        "target_role": "Product Manager",
        "dependencies": []
    }}
]
"""

def parse_json_from_llm(text: str) -> Optional[List[dict]]:
    """Try to parse JSON from LLM response, handling code blocks."""
    try:
        # Strip markdown code blocks if present
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(json)?", "", text)
            text = re.sub(r"```$", "", text)
        return json.loads(text.strip())
    except Exception as e:
        print(f"JSON Parse Error: {e}, Text: {text}")
        return None

async def decompose_tasks(message: str) -> List[dict]:
    """
    Dynamically decompose tasks using LLM.
    Fallback to hardcoded steps if LLM fails.
    """
    prompt = get_planning_prompt(message)
    try:
        response = await asyncio.to_thread(llm_engine.generate_response, prompt)
        steps = parse_json_from_llm(response)
        if steps and isinstance(steps, list):
            return steps
    except Exception as e:
        print(f"Decomposition failed: {e}")
    
    # Fallback
    return [
        {"id": "task_1", "title": I18N.t("task_1_title"), "content": I18N.t("task_1_content").format(message=message), "target_role": "Product Manager", "dependencies": []},
        {"id": "task_2", "title": I18N.t("task_2_title"), "content": I18N.t("task_2_content"), "target_role": "Architect", "dependencies": ["task_1"]},
        {"id": "task_3", "title": I18N.t("task_3_title"), "content": I18N.t("task_3_content"), "target_role": "Project Manager", "dependencies": ["task_2"]},
        {"id": "task_4", "title": I18N.t("task_4_title"), "content": I18N.t("task_4_content"), "target_role": "QA Engineer", "dependencies": ["task_3"]}
    ]

def match_agent(agents: List[dict], target_role: str) -> dict:
    """Find the best matching agent for a target role."""
    if not agents:
        return {"model_name": "server-qwen2.5-7b", "role_name": "System"}
    
    # 1. Exact match
    for a in agents:
        if a.get("role_name") == target_role:
            return a
            
    # 2. Partial match
    for a in agents:
        if target_role in a.get("role_name", ""):
            return a
            
    # 3. Default to the first agent (usually Coordinator/Manager)
    return agents[0]
