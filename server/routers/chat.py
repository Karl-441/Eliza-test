from fastapi import APIRouter, HTTPException, Depends
from server.core.config import settings
from server.core.llm import llm_engine
from server.core.memory import memory_manager
from server.core.search_engine import ai_search
from server.core.i18n import I18N
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    use_search: bool = False
    force_search: bool = False

class ChatResponse(BaseModel):
    response: str
    search_used: bool = False
    search_results: Optional[List[dict]] = None
    search_summary: Optional[str] = None
    search_query: Optional[str] = None

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    user_input = request.message
    search_context = ""
    search_used = False
    search_results = []
    search_summary = ""
    search_query = ""

    # Layer 1: Intent Recognition
    intent = ai_search.analyze_intent(user_input)
    
    # Check trigger: Force Search OR Intent Detected AND Search Enabled
    should_search = request.force_search or (settings.enable_search and intent["needs_search"])

    if should_search:
        # Layer 2: Networking
        search_query = intent["keywords"] if not request.force_search else user_input
        search_data = ai_search.execute_search(search_query)
        
        # Layer 3: Result Processing
        search_context = ai_search.process_results(search_data)
        search_results = search_data.get("raw", [])
        search_summary = search_data.get("summary", "") # Keep legacy summary format if needed
        search_used = True
    
    # Add to memory
    memory_manager.add_message("user", user_input)
    
    # Generate prompt with search context if available
    system_prompt = memory_manager.get_context_prompt()
    
    # Analyze short-term memory context
    memory_context = memory_manager.analyze_context(user_input)
    
    combined_context = ""
    if search_context:
        # Fusion Feedback
        combined_context += f"\n\n{I18N.t('chat_system_search_data')}\n{search_context}\n"
    if memory_context:
        combined_context += f"\n\n{memory_context}\n"
        
    if combined_context:
        system_prompt += combined_context + f"\n{I18N.t('chat_system_use_info')}"

    # Stream response handling would be ideal, but standard REST returns full text
    # For now, we collect the stream
    response_text = ""
    try:
        for chunk in llm_engine.stream_response(user_input, system_prompt):
            if not chunk.startswith("Error:"):
                response_text += chunk
            else:
                # Handle error in stream?
                pass
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    memory_manager.add_message("assistant", response_text)

    return ChatResponse(
        response=response_text,
        search_used=search_used,
        search_results=search_results,
        search_summary=search_summary,
        search_query=search_query
    )
