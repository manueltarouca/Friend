"""
Ollama Service for Local LLM Integration
Provides OpenAI-compatible interface for local AI processing
"""

import httpx
from typing import List, Dict, Optional, AsyncGenerator, Union
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class OllamaService:
    """Service for interacting with Ollama API for local LLM inference"""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.client = httpx.AsyncClient(timeout=300.0)
        self.default_model = os.getenv("OLLAMA_MODEL", "llama3")
        
    async def health_check(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    async def list_models(self) -> List[Dict[str, any]]:
        """List available models in Ollama"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            return response.json().get("models", [])
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        system_prompt: Optional[str] = None
    ) -> Union[Dict, AsyncGenerator]:
        """
        OpenAI-compatible chat completion
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to OLLAMA_MODEL env var)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            system_prompt: Optional system prompt to prepend
        
        Returns:
            Dict with response or async generator for streaming
        """
        model = model or self.default_model
        
        # Convert OpenAI format to Ollama format
        ollama_messages = []
        
        # Add system prompt if provided and not already in messages
        if system_prompt and (not messages or messages[0].get("role") != "system"):
            ollama_messages.append({"role": "system", "content": system_prompt})
        
        ollama_messages.extend(messages)
        
        payload = {
            "model": model,
            "messages": ollama_messages,
            "temperature": temperature,
            "stream": stream
        }
        
        if max_tokens:
            payload["options"] = {"num_predict": max_tokens}
        
        try:
            if stream:
                return self._stream_chat_completion(payload)
            else:
                response = await self.client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                
                # Convert to OpenAI-like format
                ollama_response = response.json()
                return self._format_chat_response(ollama_response, model)
                
        except Exception as e:
            logger.error(f"Ollama chat completion failed: {e}")
            raise
    
    async def _stream_chat_completion(self, payload: Dict) -> AsyncGenerator:
        """Stream chat completion responses"""
        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json=payload
        ) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        # Convert to OpenAI-like streaming format
                        yield {
                            "id": f"chatcmpl-{chunk.get('created_at', '')}",
                            "object": "chat.completion.chunk",
                            "created": int(datetime.now().timestamp()),
                            "model": payload["model"],
                            "choices": [{
                                "index": 0,
                                "delta": {
                                    "content": chunk.get("message", {}).get("content", "")
                                },
                                "finish_reason": "stop" if chunk.get("done") else None
                            }]
                        }
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse streaming response: {line}")
                        continue
    
    def _format_chat_response(self, ollama_response: Dict, model: str) -> Dict:
        """Format Ollama response to match OpenAI format"""
        message = ollama_response.get("message", {})
        
        return {
            "id": f"chatcmpl-{ollama_response.get('created_at', '')}",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": message.get("role", "assistant"),
                    "content": message.get("content", "")
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": ollama_response.get("prompt_eval_count", 0),
                "completion_tokens": ollama_response.get("eval_count", 0),
                "total_tokens": (
                    ollama_response.get("prompt_eval_count", 0) + 
                    ollama_response.get("eval_count", 0)
                )
            }
        }
    
    async def embeddings(
        self, 
        text: Union[str, List[str]], 
        model: Optional[str] = None
    ) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text
        
        Args:
            text: Single string or list of strings to embed
            model: Embedding model to use (defaults to nomic-embed-text)
        
        Returns:
            List of floats for single text, list of lists for multiple texts
        """
        model = model or os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
        
        # Handle both single and batch inputs
        texts = [text] if isinstance(text, str) else text
        single_input = isinstance(text, str)
        
        embeddings = []
        
        for t in texts:
            try:
                response = await self.client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": model, "prompt": t}
                )
                response.raise_for_status()
                
                embedding = response.json().get("embedding", [])
                embeddings.append(embedding)
                
            except Exception as e:
                logger.error(f"Failed to generate embedding: {e}")
                # Return zero vector on failure
                embeddings.append([0.0] * 384)  # Default dimension for nomic-embed-text
        
        return embeddings[0] if single_input else embeddings
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Union[str, AsyncGenerator]:
        """
        Simple text generation (non-chat)
        
        Args:
            prompt: Text prompt
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
        
        Returns:
            Generated text or async generator for streaming
        """
        model = model or self.default_model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "stream": stream
        }
        
        if max_tokens:
            payload["options"] = {"num_predict": max_tokens}
        
        try:
            if stream:
                return self._stream_generate(payload)
            else:
                response = await self.client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                return response.json().get("response", "")
                
        except Exception as e:
            logger.error(f"Ollama generate failed: {e}")
            raise
    
    async def _stream_generate(self, payload: Dict) -> AsyncGenerator:
        """Stream generation responses"""
        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/generate",
            json=payload
        ) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        yield chunk.get("response", "")
                    except json.JSONDecodeError:
                        continue
    
    async def pull_model(self, model_name: str) -> bool:
        """
        Pull a model from Ollama library
        
        Args:
            model_name: Name of the model to pull
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name}
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()