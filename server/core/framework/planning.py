import json
import re
import asyncio
from typing import List, Optional
from server.core.llm import llm_engine

PLANNING_PROMPT_TEMPLATE = """
作为高级项目经理，请将以下用户需求拆解为 3-5 个具体的执行步骤。
用户需求：{message}

请仅返回一个 JSON 数组，格式如下，不要包含 markdown 代码块标记：
[
    {{
        "id": "task_1",
        "title": "步骤名称",
        "content": "详细的任务描述",
        "target_role": "推荐的角色名称",
        "dependencies": [] // 依赖的任务ID列表，例如 ["task_0"]
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
    prompt = PLANNING_PROMPT_TEMPLATE.format(message=message)
    try:
        response = await asyncio.to_thread(llm_engine.generate_response, prompt)
        steps = parse_json_from_llm(response)
        if steps and isinstance(steps, list):
            return steps
    except Exception as e:
        print(f"Decomposition failed: {e}")
    
    # Fallback
    return [
        {"id": "task_1", "title": "需求理解", "content": f"分析用户需求：{message}", "target_role": "产品经理", "dependencies": []},
        {"id": "task_2", "title": "方案设计", "content": "提出可行的技术与创意方案", "target_role": "架构师", "dependencies": ["task_1"]},
        {"id": "task_3", "title": "分配执行", "content": "将任务分配到对应角色", "target_role": "项目经理", "dependencies": ["task_2"]},
        {"id": "task_4", "title": "整合评审", "content": "收集输出并生成综合报告", "target_role": "测试工程师", "dependencies": ["task_3"]}
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
