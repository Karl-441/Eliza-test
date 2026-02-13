import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from .agent import BaseAgent
from .events import Event
from .bus import message_bus
from server.core.llm import llm_engine
from server.core.tools import get_tool_descriptions, execute_tool
from server.core.framework.planning import decompose_tasks
from server.core.database import SessionLocal
from server.core.models import WorkflowState
from server.core.i18n import I18N

class GenericLLMAgent(BaseAgent):
    def __init__(self, agent_id: str, role: str, model_name: str, system_prompt: str, project_id: str):
        super().__init__(agent_id, role, description=system_prompt)
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.project_id = project_id

    async def process_task(self, event: Event):
        # We only care about tasks for this project
        if event.data.get("project_id") != self.project_id:
            return

        task_id = event.data.get("task_id")
        task_content = event.data.get("content")
        context = event.data.get("context", "")
        
        start_time = time.time()

        # Notify Start
        await self.send_event(
            target_topic="orchestrator",
            type="task.started",
            data={
                "task_id": task_id,
                "role": self.role,
                "status": "step_start", # Frontend compat
                "project_id": self.project_id,
                "step_index": event.data.get("step_index", 0),
                "task": event.data.get("task_title", ""),
                "start_time": start_time
            },
            correlation_id=event.correlation_id
        )

        try:
            # Build Prompt
            tool_descriptions = get_tool_descriptions()
            full_prompt = f"""
{I18N.t('agent_identity').format(role=self.role)}
{I18N.t('agent_task').format(content=task_content)}

{I18N.t('agent_context')}
{context}

{I18N.t('agent_tools')}
{tool_descriptions}

{I18N.t('agent_instruction')}
{I18N.t('agent_instruction_detail')}
"""
            # Call LLM
            # Note: In real system, we should pass model_name to llm_engine
            gen = await asyncio.to_thread(llm_engine.generate_response, full_prompt)
            
            # Tool Execution Logic (Simplified)
            # In a robust system, this should be a loop or handled by a ToolManager
            try:
                # Basic JSON parsing for tool
                if "{" in gen and "}" in gen and "tool" in gen:
                     # Very naive extraction, should use the parser from orchestrator
                     import re
                     json_str = gen[gen.find("{"):gen.rfind("}")+1]
                     tool_call = json.loads(json_str)
                     if "tool" in tool_call:
                         tool_name = tool_call["tool"]
                         params = tool_call.get("params", {})
                         tool_result = execute_tool(tool_name, **params)
                         gen = f"Tool Executed: {tool_name}\nResult: {tool_result}\n\nAnalysis: {gen}"
            except Exception as e:
                pass # Tool execution failed or wasn't a tool call

            end_time = time.time()
            duration = end_time - start_time

            # Notify Completion
            await self.send_event(
                target_topic="orchestrator",
                type="task.completed",
                data={
                    "task_id": task_id,
                    "output": gen,
                    "role": self.role,
                    "status": "step_done", # Frontend compat
                    "project_id": self.project_id,
                    "step_index": event.data.get("step_index", 0),
                    "duration": duration,
                    "model": self.model_name
                },
                correlation_id=event.correlation_id
            )

        except Exception as e:
            await self.send_event(
                target_topic="orchestrator",
                type="task.failed",
                data={
                    "task_id": task_id,
                    "error": str(e),
                    "project_id": self.project_id
                },
                correlation_id=event.correlation_id
            )

    async def process_message(self, event: Event):
        pass

class OrchestratorAgent(BaseAgent):
    def __init__(self, agent_id: str, project_id: str, api_key: str, agents_metadata: List[dict], workflow_id: str = None):
        super().__init__(agent_id, "admin", description="Orchestrator")
        self.project_id = project_id
        self.api_key = api_key
        self.agents_metadata = agents_metadata
        self.tasks: List[dict] = []
        self.outputs: List[dict] = []
        self.context = ""
        self.correlation_id = None
        self.workflow_id = workflow_id
        self.status = "idle" # idle, running, paused, completed, failed

    async def on_start(self):
        message_bus.subscribe("orchestrator", self._handle_direct)
        if self.workflow_id:
            await self._load_state()

    async def _save_state(self):
        if not self.workflow_id:
            return
        
        db = SessionLocal()
        try:
            state = db.query(WorkflowState).filter(WorkflowState.id == self.workflow_id).first()
            if not state:
                state = WorkflowState(id=self.workflow_id, project_id=self.project_id)
                db.add(state)
            
            state.status = self.status
            state.tasks = json.dumps(self.tasks, ensure_ascii=False)
            state.context = self.context
            state.outputs = json.dumps(self.outputs, ensure_ascii=False)
            db.commit()
        except Exception as e:
            print(f"Error saving state: {e}")
        finally:
            db.close()

    async def _load_state(self):
        if not self.workflow_id:
            return

        db = SessionLocal()
        try:
            state = db.query(WorkflowState).filter(WorkflowState.id == self.workflow_id).first()
            if state:
                self.status = state.status
                self.tasks = json.loads(state.tasks) if state.tasks else []
                self.context = state.context or ""
                self.outputs = json.loads(state.outputs) if state.outputs else []
                # If we loaded a running state, try to resume dispatch
                if self.status == "running":
                    asyncio.create_task(self.dispatch_next_task())
        except Exception as e:
            print(f"Error loading state: {e}")
        finally:
            db.close()

    async def process_message(self, event: Event):
        if event.type == "orchestration.start":
            self.correlation_id = event.correlation_id
            message = event.data.get("message")
            await self.start_workflow(message)
        elif event.type == "orchestration.control":
            # Check if this control message is for this project
            if event.data.get("project_id") != self.project_id:
                return

            action = event.data.get("action")
            if action == "pause":
                await self.pause_workflow()
            elif action == "resume":
                await self.resume_workflow()
            elif action == "approve":
                await self.handle_approval(True, event.data.get("message"))
            elif action == "reject":
                await self.handle_approval(False, event.data.get("message"))

    async def handle_approval(self, approved: bool, message: str = None):
        if self.status != "waiting_for_approval":
            return

        if approved:
            self.status = "running"
            await self.send_event("monitor", "orchestration.status", {
                "type": "orchestration",
                "status": "approved",
                "project_id": self.project_id,
                "message": "人工审批通过，继续执行。",
                "api_key": self.api_key
            }, correlation_id=self.correlation_id)
            await self._save_state()
            await self.dispatch_next_task()
        else:
            self.status = "failed" # Or cancelled
            await self.send_event("monitor", "orchestration.status", {
                "type": "orchestration",
                "status": "rejected",
                "project_id": self.project_id,
                "message": f"人工审批驳回: {message or '无理由'}",
                "api_key": self.api_key
            }, correlation_id=self.correlation_id)
            await self._save_state()

    async def process_task(self, event: Event):
        pass

    async def start_workflow(self, message: str):
        self.status = "running"
        if not self.workflow_id:
            # Generate a workflow ID if not provided (though usually provided by caller)
            import uuid
            self.workflow_id = str(uuid.uuid4())

        await self.send_event("monitor", "orchestration.status", {
            "type": "orchestration",
            "status": "start",
            "project_id": self.project_id,
            "message": "开始分析需求...",
            "api_key": self.api_key,
            "workflow_id": self.workflow_id
        }, correlation_id=self.correlation_id)

        self.tasks = await decompose_tasks(message)
        # Initialize task status
        for i, t in enumerate(self.tasks):
            t['status'] = 'pending'
            t['retry_count'] = 0  # Initialize retry count
            if 'id' not in t:
                t['id'] = f"task-{i}" # Fallback ID

        await self._save_state()

        await self.send_event("monitor", "orchestration.status", {
            "type": "orchestration",
            "status": "plan_created",
            "project_id": self.project_id,
            "tasks": self.tasks,
            "api_key": self.api_key
        }, correlation_id=self.correlation_id)

        # Request Approval for the Plan
        await self.ask_for_approval("plan_review", {
            "title": I18N.t("task_plan_approval_title"),
            "description": I18N.t("task_plan_approval_desc"),
            "data": self.tasks
        })

    async def ask_for_approval(self, approval_id: str, context: dict):
        self.status = "waiting_for_approval"
        self.approval_context = {
            "id": approval_id,
            "context": context,
            "timestamp": time.time()
        }
        await self._save_state()
        
        await self.send_event("monitor", "orchestration.status", {
            "type": "orchestration",
            "status": "waiting_for_approval",
            "project_id": self.project_id,
            "approval_id": approval_id,
            "approval_context": context,
            "message": I18N.t("waiting_approval"),
            "api_key": self.api_key
        }, correlation_id=self.correlation_id)

    async def dispatch_next_task(self):
        if self.status != "running":
            return

        all_completed = True
        dispatched_any = False

        for i, task in enumerate(self.tasks):
            if task.get('status') == 'pending':
                all_completed = False
                # Check dependencies
                deps = task.get('dependencies', [])
                deps_met = True
                for dep_id in deps:
                    # Find dependency task
                    dep_task = next((t for t in self.tasks if t.get('id') == dep_id), None)
                    # If dep not found or not completed, wait
                    if not dep_task or dep_task.get('status') != 'completed':
                        deps_met = False
                        break
                
                if deps_met:
                    # Dispatch
                    task['status'] = 'running'
                    await self._dispatch_single_task(task, i)
                    dispatched_any = True
            
            elif task.get('status') == 'running':
                all_completed = False

        if all_completed:
            await self.finish_workflow()
        
        if dispatched_any:
            await self._save_state()

    async def _dispatch_single_task(self, task: dict, index: int):
        target_role = task.get("target_role", "总负责人")
        assigned_agent = self.match_agent(target_role)
        role_topic = f"role.{assigned_agent['role_name']}"

        await self.send_event("monitor", "orchestration.status", {
            "type": "orchestration",
            "status": "step_start",
            "project_id": self.project_id,
            "step_index": index,
            "task_id": task.get('id'),
            "role": assigned_agent['role_name'],
            "task": task['title'],
            "api_key": self.api_key
        }, correlation_id=self.correlation_id)

        await self.send_event(role_topic, "task.created", {
            "task_id": task.get('id'),
            "project_id": self.project_id,
            "content": task['content'],
            "task_title": task['title'],
            "context": self.context,
            "step_index": index
        }, correlation_id=self.correlation_id)

    async def handle_task_completed(self, event: Event):
        data = event.data
        task_id = data.get("task_id")
        
        # Find task
        task = next((t for t in self.tasks if t.get('id') == task_id), None)
        if not task:
            return

        output = data.get("output", "")
        role = data.get("role", "unknown")
        
        task['status'] = 'completed'
        task['output'] = output
        task['performer'] = role
        if 'duration' in data:
            task['duration'] = data['duration']
        if 'model' in data:
            task['model'] = data['model']

        self.outputs.append({
            "role": role,
            "task": task['title'],
            "content": output
        })
        self.context += f"\n[{role}]: {output}\n"
        
        await self._save_state()

        await self.send_event("monitor", "orchestration.status", {
            "type": "orchestration",
            "status": "step_done",
            "project_id": self.project_id,
            "step_index": self.tasks.index(task),
            "task_id": task_id,
            "role": role,
            "output": output[:200] + "...",
            "api_key": self.api_key
        }, correlation_id=self.correlation_id)

        await self.dispatch_next_task()

    async def handle_task_failed(self, event: Event):
        task_id = event.data.get("task_id")
        task = next((t for t in self.tasks if t.get('id') == task_id), None)
        
        if not task:
            return

        MAX_RETRIES = 3
        current_retries = task.get('retry_count', 0)
        
        if current_retries < MAX_RETRIES:
            # Retry logic
            task['retry_count'] = current_retries + 1
            task['status'] = 'pending' # Reset status to pending so it can be picked up again
            
            error_msg = event.data.get("error")
            warning_msg = f"Task {task['title']} failed (Attempt {current_retries + 1}/{MAX_RETRIES}). Error: {error_msg}. Retrying..."
            
            await self.send_event("monitor", "orchestration.status", {
                "type": "orchestration",
                "status": "warning",
                "project_id": self.project_id,
                "message": warning_msg,
                "api_key": self.api_key
            }, correlation_id=self.correlation_id)
            
            await self._save_state()
            # Wait a bit before retry? 
            await asyncio.sleep(2) 
            await self.dispatch_next_task()
            return

        # Final failure
        task['status'] = 'failed'
        task['error'] = event.data.get("error")
        await self._save_state()

        await self.send_event("monitor", "orchestration.status", {
            "type": "orchestration",
            "status": "error",
            "project_id": self.project_id,
            "message": f"Task failed after {MAX_RETRIES} attempts: {event.data.get('error')}",
            "api_key": self.api_key
        }, correlation_id=self.correlation_id)

    async def pause_workflow(self):
        self.status = "paused"
        await self._save_state()
        await self.send_event("monitor", "orchestration.status", {
            "type": "orchestration",
            "status": "paused",
            "project_id": self.project_id,
            "message": "Workflow paused.",
            "api_key": self.api_key
        }, correlation_id=self.correlation_id)

    async def resume_workflow(self):
        self.status = "running"
        await self._save_state()
        await self.send_event("monitor", "orchestration.status", {
            "type": "orchestration",
            "status": "resumed",
            "project_id": self.project_id,
            "message": "Workflow resumed.",
            "api_key": self.api_key
        }, correlation_id=self.correlation_id)
        await self.dispatch_next_task()

    async def finish_workflow(self):
        self.status = "completed"
        await self._save_state()

        await self.send_event("monitor", "orchestration.status", {
            "type": "orchestration",
            "status": "generating_report",
            "project_id": self.project_id,
            "message": "正在生成总结报告...",
            "api_key": self.api_key
        }, correlation_id=self.correlation_id)
        
        report_text = "\n".join([f"[{o['role']}] {o['task']}: {o['content']}" for o in self.outputs])
        prompt = f"作为总负责人，请根据以下各角色的工作输出，生成一份最终的总结报告：\n{report_text}"
        
        report = await asyncio.to_thread(llm_engine.generate_response, prompt)

        await self.send_event("monitor", "orchestration.status", {
            "type": "orchestration",
            "status": "complete",
            "project_id": self.project_id,
            "report": report,
            "api_key": self.api_key
        }, correlation_id=self.correlation_id)

    async def _handle_direct(self, event: Event):
        if event.type == "task.completed":
            await self.handle_task_completed(event)
        elif event.type == "task.failed":
            await self.handle_task_failed(event)
        else:
            await super()._handle_direct(event)

    def match_agent(self, target_role: str) -> dict:
        if not self.agents_metadata:
            return {"role_name": "System"}
        for a in self.agents_metadata:
            if a.get("role_name") == target_role:
                return a
        for a in self.agents_metadata:
            if target_role in a.get("role_name", ""):
                return a
        return self.agents_metadata[0]
