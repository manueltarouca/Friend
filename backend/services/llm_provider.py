"""
LLM Provider Abstraction Layer
Allows switching between different LLM providers (Ollama, OpenAI, etc.)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Union, AsyncGenerator
import os
import logging
from backend.services.ollama_service import OllamaService

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[Dict, AsyncGenerator]:
        """Generate chat completion"""
        pass
    
    @abstractmethod
    async def embeddings(
        self,
        text: Union[str, List[str]],
        model: Optional[str] = None
    ) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for text"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the service is available"""
        pass

class OllamaProvider(LLMProvider):
    """Ollama provider for local LLM inference"""
    
    def __init__(self, base_url: Optional[str] = None):
        self.service = OllamaService(base_url)
        self.default_model = os.getenv("OLLAMA_MODEL", "llama3")
        self.embedding_model = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[Dict, AsyncGenerator]:
        """Generate chat completion using Ollama"""
        model = model or self.default_model
        return await self.service.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            **kwargs
        )
    
    async def embeddings(
        self,
        text: Union[str, List[str]],
        model: Optional[str] = None
    ) -> Union[List[float], List[List[float]]]:
        """Generate embeddings using Ollama"""
        model = model or self.embedding_model
        return await self.service.embeddings(text, model)
    
    async def health_check(self) -> bool:
        """Check if Ollama is available"""
        return await self.service.health_check()
    
    async def list_models(self) -> List[Dict[str, any]]:
        """List available Ollama models"""
        return await self.service.list_models()

class OpenAIProvider(LLMProvider):
    """OpenAI provider for cloud-based LLM inference"""
    
    def __init__(self, api_key: Optional[str] = None):
        # Import only when needed to avoid dependency if not using OpenAI
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
            self.available = True
        except ImportError:
            logger.warning("OpenAI package not installed")
            self.available = False
        
        self.default_model = os.getenv("OPENAI_MODEL", "gpt-4")
        self.embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[Dict, AsyncGenerator]:
        """Generate chat completion using OpenAI"""
        if not self.available:
            raise RuntimeError("OpenAI provider not available")
        
        model = model or self.default_model
        
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            **kwargs
        )
        
        if stream:
            return response
        else:
            return response.model_dump()
    
    async def embeddings(
        self,
        text: Union[str, List[str]],
        model: Optional[str] = None
    ) -> Union[List[float], List[List[float]]]:
        """Generate embeddings using OpenAI"""
        if not self.available:
            raise RuntimeError("OpenAI provider not available")
        
        model = model or self.embedding_model
        
        # Handle both single and batch inputs
        inputs = [text] if isinstance(text, str) else text
        
        response = await self.client.embeddings.create(
            model=model,
            input=inputs
        )
        
        embeddings = [item.embedding for item in response.data]
        
        return embeddings[0] if isinstance(text, str) else embeddings
    
    async def health_check(self) -> bool:
        """Check if OpenAI API is available"""
        if not self.available:
            return False
        
        try:
            # Try a simple API call
            await self.client.models.list()
            return True
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return False

class LLMProviderFactory:
    """Factory for creating LLM providers"""
    
    _providers = {
        "ollama": OllamaProvider,
        "openai": OpenAIProvider,
    }
    
    @classmethod
    def register_provider(cls, name: str, provider_class: type):
        """Register a new provider type"""
        cls._providers[name] = provider_class
    
    @classmethod
    def create_provider(
        cls,
        provider_type: str = None,
        **kwargs
    ) -> LLMProvider:
        """
        Create an LLM provider instance
        
        Args:
            provider_type: Type of provider (ollama, openai, etc.)
            **kwargs: Additional arguments for provider initialization
        
        Returns:
            LLMProvider instance
        """
        provider_type = provider_type or os.getenv("LLM_PROVIDER", "ollama")
        
        if provider_type not in cls._providers:
            raise ValueError(
                f"Unknown provider type: {provider_type}. "
                f"Available: {list(cls._providers.keys())}"
            )
        
        provider_class = cls._providers[provider_type]
        return provider_class(**kwargs)

# Singleton instance for default provider
_default_provider = None

def get_default_llm_provider() -> LLMProvider:
    """Get the default LLM provider instance"""
    global _default_provider
    
    if _default_provider is None:
        _default_provider = LLMProviderFactory.create_provider()
    
    return _default_provider

async def set_default_llm_provider(provider: LLMProvider):
    """Set the default LLM provider instance"""
    global _default_provider
    _default_provider = provider