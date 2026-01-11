from typing import List, Dict
import datetime
from .projects import projects_store
from .llm import LLMEngine
from .monitor import monitor_hub
from .users import user_manager

llm_engine = LLMEngine()

def decompose_tasks(message: str) -> List[dict]:
    steps = [
        {"title": "需求理解", "content": f"分析用户需求：{message}"},
        {"title": "方案设计", "content": "提出可行的技术与创意方案"},
        {"title": "分配执行", "content": "将任务分配到对应角色"},
        {"title": "整合评审", "content": "收集输出并生成综合报告"}
    ]
    return steps

async def orchestrate(project_id: str, message: str, api_key: str) -> Dict[str, any]:
    agents = projects_store.list_agents(project_id).get("agents", [])
    outputs: List[dict] = []
    tasks = decompose_tasks(message)
    for i, t in enumerate(tasks):
        target_role = "总负责人" if i == 0 else ("技术负责人" if i == 1 else ("执行助手" if i == 2 else "评审助手"))
        target = next((a for a in agents if a.get("role_name") == target_role), None)
        model = (target or {"model_name": "server-qwen2.5-7b"}).get("model_name")
        content = f"[{t['title']}] {t['content']}"
        try:
            gen = llm_engine.generate_response(content)
        except:
            gen = content
        item = {"project_id": project_id, "model": model, "role": target_role, "content": gen, "timestamp": datetime.datetime.now().isoformat()}
        outputs.append(item)
        projects_store.add_log(project_id, item)
        user = next((u for u in user_manager.users.values() if u.client_secret == api_key), None)
        role = user.role if user else "guest"
        await monitor_hub.broadcast(api_key, role, item)
    report_text = "；".join([o["content"] for o in outputs])
    try:
        report = llm_engine.generate_response(f"整合以下模块输出，形成简洁报告：{report_text}")
    except:
        report = report_text
    return {"outputs": outputs, "report": report}
