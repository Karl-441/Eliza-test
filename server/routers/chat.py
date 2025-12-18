from fastapi import APIRouter, HTTPException, Depends
from server.core.config import settings
from server.core.llm import llm_engine
from server.core.memory import memory_manager
from server.core.search import search_engine
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

    # Check for manual search trigger or automatic keyword match
    if request.force_search or (settings.enable_search and search_engine.should_search(user_input)):
        search_query = user_input
        search_data = search_engine.search(user_input)
        search_context = search_data.get("summary", "")
        search_summary = search_context
        search_results = search_data.get("raw", [])
        search_used = True
    
    # Add to memory
    memory_manager.add_message("user", user_input)
    
    # Generate prompt with search context if available
    system_prompt = memory_manager.get_context_prompt()
    
    # Analyze short-term memory context
    memory_context = memory_manager.analyze_context(user_input)
    
    combined_context = ""
    if search_context:
        combined_context += f"\n\nRelevant Information from Search:\n{search_context}\n"
    if memory_context:
        combined_context += f"\n\n{memory_context}\n"
        
    if combined_context:
        system_prompt += combined_context + "\nUse this information to answer the user."

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
