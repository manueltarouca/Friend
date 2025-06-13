"""
Local Chat Router - Privacy-focused chat using Ollama
This is a proof of concept for using local LLMs instead of cloud services
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

import database.chat as chat_db
from models.chat import ChatSession, Message, SendMessageRequest, MessageSender, ResponseMessage
from utils.other import endpoints as auth
from backend.services.llm_provider import get_default_llm_provider, LLMProviderFactory
from utils.llms.memory import get_prompt_memories

router = APIRouter()

# Initialize Ollama provider
llm_provider = LLMProviderFactory.create_provider("ollama")

async def process_chat_message_local(
    uid: str,
    message: str,
    chat_session: ChatSession,
    plugin_id: Optional[str] = None
) -> str:
    """Process chat message using local LLM (Ollama)"""
    
    # Get user context
    user_name, memories_str = get_prompt_memories(uid)
    
    # Build conversation history
    messages = []
    
    # System prompt
    system_prompt = f"""You are 'Omi', a friendly and helpful AI assistant running locally on the user's device.
You are privacy-focused and all processing happens locally - no data is sent to external servers.
You know the following about {user_name}: {memories_str}

Be helpful, friendly, and concise in your responses."""
    
    messages.append({"role": "system", "content": system_prompt})
    
    # Add conversation history
    for msg in chat_session.messages[-10:]:  # Last 10 messages for context
        role = "user" if msg.sender == MessageSender.human else "assistant"
        messages.append({"role": role, "content": msg.text})
    
    # Add current message
    messages.append({"role": "user", "content": message})
    
    # Get response from Ollama
    try:
        response = await llm_provider.chat_completion(
            messages=messages,
            model="llama3",  # or any other local model
            temperature=0.7,
            max_tokens=500
        )
        
        # Extract the response content
        if isinstance(response, dict):
            return response["choices"][0]["message"]["content"]
        else:
            return str(response)
            
    except Exception as e:
        print(f"Error with local LLM: {e}")
        # Fallback response
        return "I'm having trouble processing your request locally. Please check that Ollama is running."

async def stream_chat_message_local(
    uid: str,
    message: str,
    chat_session: ChatSession,
    plugin_id: Optional[str] = None
):
    """Stream chat response using local LLM"""
    
    # Get user context
    user_name, memories_str = get_prompt_memories(uid)
    
    # Build conversation history
    messages = []
    
    # System prompt
    system_prompt = f"""You are 'Omi', a friendly and helpful AI assistant running locally on the user's device.
You are privacy-focused and all processing happens locally - no data is sent to external servers.
You know the following about {user_name}: {memories_str}

Be helpful, friendly, and concise in your responses."""
    
    messages.append({"role": "system", "content": system_prompt})
    
    # Add conversation history
    for msg in chat_session.messages[-10:]:
        role = "user" if msg.sender == MessageSender.human else "assistant"
        messages.append({"role": role, "content": msg.text})
    
    # Add current message
    messages.append({"role": "user", "content": message})
    
    # Stream response from Ollama
    try:
        stream = await llm_provider.chat_completion(
            messages=messages,
            model="llama3",
            temperature=0.7,
            max_tokens=500,
            stream=True
        )
        
        async for chunk in stream:
            if isinstance(chunk, dict) and "choices" in chunk:
                content = chunk["choices"][0].get("delta", {}).get("content", "")
                if content:
                    yield content
            else:
                yield str(chunk)
                
    except Exception as e:
        print(f"Error streaming from local LLM: {e}")
        yield "I'm having trouble streaming the response. Please check Ollama."

@router.post("/v1/chat/send-message/local", response_model=ResponseMessage, tags=['chat'])
async def send_message_local(
    data: SendMessageRequest,
    uid: str = Depends(auth.get_user_id)
):
    """Send a chat message using local LLM processing"""
    
    # Check if Ollama is available
    if not await llm_provider.health_check():
        raise HTTPException(
            status_code=503,
            detail="Local LLM service (Ollama) is not available. Please ensure Ollama is running."
        )
    
    # Get or create chat session
    chat_session = chat_db.get_chat_session(uid, app_id=data.plugin_id)
    if chat_session is None:
        chat_session = ChatSession(
            id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc),
            plugin_id=data.plugin_id
        )
        chat_db.create_chat_session(uid, chat_session)
    
    # Create user message
    user_message = Message(
        id=str(uuid.uuid4()),
        created_at=datetime.now(timezone.utc),
        sender=MessageSender.human,
        text=data.text
    )
    
    # Process message locally
    ai_response = await process_chat_message_local(
        uid=uid,
        message=data.text,
        chat_session=chat_session,
        plugin_id=data.plugin_id
    )
    
    # Create AI message
    ai_message = Message(
        id=str(uuid.uuid4()),
        created_at=datetime.now(timezone.utc),
        sender=MessageSender.ai,
        text=ai_response,
        plugin_id=data.plugin_id
    )
    
    # Save messages
    chat_session.messages.extend([user_message, ai_message])
    chat_db.update_chat_session(uid, chat_session)
    
    return ResponseMessage(message=ai_message)

@router.post("/v1/chat/send-message/local/stream", tags=['chat'])
async def send_message_stream_local(
    data: SendMessageRequest,
    uid: str = Depends(auth.get_user_id)
):
    """Stream chat response using local LLM"""
    
    # Check if Ollama is available
    if not await llm_provider.health_check():
        raise HTTPException(
            status_code=503,
            detail="Local LLM service (Ollama) is not available. Please ensure Ollama is running."
        )
    
    # Get or create chat session
    chat_session = chat_db.get_chat_session(uid, app_id=data.plugin_id)
    if chat_session is None:
        chat_session = ChatSession(
            id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc),
            plugin_id=data.plugin_id
        )
        chat_db.create_chat_session(uid, chat_session)
    
    # Create user message
    user_message = Message(
        id=str(uuid.uuid4()),
        created_at=datetime.now(timezone.utc),
        sender=MessageSender.human,
        text=data.text
    )
    
    # Save user message
    chat_session.messages.append(user_message)
    chat_db.update_chat_session(uid, chat_session)
    
    # Stream response
    async def generate():
        full_response = ""
        async for chunk in stream_chat_message_local(
            uid=uid,
            message=data.text,
            chat_session=chat_session,
            plugin_id=data.plugin_id
        ):
            full_response += chunk
            yield chunk
        
        # Save AI message after streaming completes
        ai_message = Message(
            id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc),
            sender=MessageSender.ai,
            text=full_response,
            plugin_id=data.plugin_id
        )
        chat_session.messages.append(ai_message)
        chat_db.update_chat_session(uid, chat_session)
    
    return StreamingResponse(generate(), media_type="text/plain")

@router.get("/v1/chat/local/health", tags=['chat'])
async def health_check():
    """Check if local LLM service is available"""
    is_healthy = await llm_provider.health_check()
    
    if is_healthy:
        # Get available models
        models = []
        if hasattr(llm_provider, 'list_models'):
            models = await llm_provider.list_models()
        
        return {
            "status": "healthy",
            "provider": "ollama",
            "models": models
        }
    else:
        raise HTTPException(
            status_code=503,
            detail="Local LLM service is not available"
        )