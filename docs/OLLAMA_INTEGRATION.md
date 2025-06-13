# Ollama Integration for OMI Privacy Fork

## Overview

This document outlines the integration of Ollama as the local LLM provider for the privacy-focused OMI fork, replacing cloud-based AI services like OpenAI.

## Architecture

### Current Flow
```
Mobile App → Backend → OpenAI/Anthropic API
                    → Deepgram/Soniox STT
                    → External Embeddings
```

### New Local Flow
```
Mobile App → Local Backend → Ollama API (LLM)
                          → Whisper.cpp (STT)
                          → Local Embeddings
```

## Implementation Plan

### Phase 1: Backend Ollama Integration

#### 1.1 Ollama Service Wrapper

Create a new service that wraps Ollama's API to match the existing OpenAI interface:

```python
# backend/services/ollama_service.py
import httpx
from typing import List, Dict, Optional
import json

class OllamaService:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=300.0)
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "llama3",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ):
        """OpenAI-compatible chat completion"""
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream
        }
        
        if max_tokens:
            payload["options"] = {"num_predict": max_tokens}
        
        if stream:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        yield json.loads(line)
        else:
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            return response.json()
    
    async def embeddings(self, text: str, model: str = "nomic-embed-text"):
        """Generate embeddings locally"""
        response = await self.client.post(
            f"{self.base_url}/api/embeddings",
            json={"model": model, "prompt": text}
        )
        return response.json()["embedding"]
```

#### 1.2 Update LLM Provider Interface

Create an abstraction layer for LLM providers:

```python
# backend/services/llm_provider.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from backend.services.ollama_service import OllamaService
from backend.services.openai_service import OpenAIService

class LLMProvider(ABC):
    @abstractmethod
    async def chat_completion(self, messages, model, **kwargs):
        pass
    
    @abstractmethod
    async def embeddings(self, text, model=None):
        pass

class OllamaProvider(LLMProvider):
    def __init__(self):
        self.service = OllamaService()
    
    async def chat_completion(self, messages, model="llama3", **kwargs):
        return await self.service.chat_completion(messages, model, **kwargs)
    
    async def embeddings(self, text, model="nomic-embed-text"):
        return await self.service.embeddings(text, model)

class OpenAIProvider(LLMProvider):
    def __init__(self):
        self.service = OpenAIService()
    
    async def chat_completion(self, messages, model="gpt-4", **kwargs):
        return await self.service.chat_completion(messages, model, **kwargs)
    
    async def embeddings(self, text, model="text-embedding-ada-002"):
        return await self.service.embeddings(text, model)

# Factory function
def get_llm_provider(provider_type: str = "ollama") -> LLMProvider:
    if provider_type == "ollama":
        return OllamaProvider()
    elif provider_type == "openai":
        return OpenAIProvider()
    else:
        raise ValueError(f"Unknown provider: {provider_type}")
```

### Phase 2: Memory Processing Updates

#### 2.1 Update Memory Creation

Modify the memory processing pipeline to use local models:

```python
# backend/routers/memories.py (modifications)
from backend.services.llm_provider import get_llm_provider

llm_provider = get_llm_provider(os.getenv("LLM_PROVIDER", "ollama"))

async def _process_memory_with_llm(
    uid: str,
    language_code: str,
    memory: Union[CreateMemory, MemorySource],
) -> Tuple[str, str, str]:
    # Existing prompt construction...
    
    # Use local LLM instead of OpenAI
    response = await llm_provider.chat_completion(
        messages=[{"role": "system", "content": prompt}],
        model=os.getenv("OLLAMA_MODEL", "llama3"),
        temperature=0.5,
        max_tokens=2000
    )
    
    # Process response...
```

#### 2.2 Update Embeddings

Replace OpenAI embeddings with local embeddings:

```python
# backend/services/vector_db.py (modifications)
async def create_embedding(text: str) -> List[float]:
    llm_provider = get_llm_provider(os.getenv("LLM_PROVIDER", "ollama"))
    return await llm_provider.embeddings(text)
```

### Phase 3: Speech-to-Text Integration

#### 3.1 Whisper.cpp Service

Create a service for local STT using whisper.cpp:

```python
# backend/services/whisper_service.py
import asyncio
import subprocess
import tempfile
import os
from typing import Optional

class WhisperService:
    def __init__(self, model_path: str = "./models/whisper"):
        self.model_path = model_path
        self.model_size = os.getenv("WHISPER_MODEL", "base")
    
    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        sample_rate: int = 16000
    ) -> str:
        """Transcribe audio using whisper.cpp"""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_file.write(audio_data)
            tmp_path = tmp_file.name
        
        try:
            cmd = [
                "./whisper.cpp/main",
                "-m", f"{self.model_path}/ggml-{self.model_size}.bin",
                "-f", tmp_path,
                "--no-timestamps",
                "--print-colors", "false"
            ]
            
            if language:
                cmd.extend(["-l", language])
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Whisper failed: {stderr.decode()}")
            
            return stdout.decode().strip()
        finally:
            os.unlink(tmp_path)
```

### Phase 4: Configuration & Deployment

#### 4.1 Docker Compose Setup

Create a complete local deployment:

```yaml
# docker-compose.yml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    command: serve

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - LLM_PROVIDER=ollama
      - OLLAMA_HOST=http://ollama:11434
      - WHISPER_MODEL=base
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://user:password@postgres:5432/omi
    depends_on:
      - ollama
      - redis
      - postgres
    volumes:
      - ./models:/app/models

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=omi
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  whisper:
    build: ./whisper
    volumes:
      - ./models/whisper:/models
      - audio_queue:/audio

volumes:
  ollama_data:
  redis_data:
  postgres_data:
  audio_queue:
```

#### 4.2 Model Management

Create a script to download and manage models:

```bash
#!/bin/bash
# scripts/setup_models.sh

echo "Setting up local AI models..."

# Pull Ollama models
echo "Pulling Ollama models..."
docker exec ollama ollama pull llama3
docker exec ollama ollama pull nomic-embed-text
docker exec ollama ollama pull codellama  # For code-related tasks

# Download Whisper models
echo "Downloading Whisper models..."
mkdir -p models/whisper
cd models/whisper

# Download base model (good balance of speed/quality)
wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin

# Optional: Download other model sizes
# wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin
# wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin
# wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin

cd ../..

echo "Model setup complete!"
```

### Phase 5: Flutter App Updates

#### 5.1 Backend Discovery

Update the app to discover local backend:

```dart
// app/lib/services/backend_discovery.dart
import 'dart:io';
import 'package:multicast_dns/multicast_dns.dart';

class BackendDiscovery {
  static const String serviceName = '_omi-backend._tcp.local';
  
  static Future<String?> discoverBackend() async {
    if (Platform.isIOS || Platform.isMacOS || Platform.isAndroid) {
      final MDnsClient client = MDnsClient();
      await client.start();
      
      try {
        await for (final PtrResourceRecord ptr in client.lookup<PtrResourceRecord>(
          ResourceRecordQuery.serverPointer(serviceName),
        ).timeout(Duration(seconds: 5))) {
          
          await for (final SrvResourceRecord srv in client.lookup<SrvResourceRecord>(
            ResourceRecordQuery.service(ptr.domainName),
          )) {
            return 'http://${srv.target}:${srv.port}';
          }
        }
      } catch (e) {
        print('mDNS discovery failed: $e');
      } finally {
        client.stop();
      }
    }
    
    // Fallback to manual configuration
    return null;
  }
}
```

#### 5.2 Settings Update

Add local backend configuration:

```dart
// app/lib/pages/settings/backend_settings.dart
class BackendSettingsPage extends StatefulWidget {
  @override
  _BackendSettingsPageState createState() => _BackendSettingsPageState();
}

class _BackendSettingsPageState extends State<BackendSettingsPage> {
  final _controller = TextEditingController();
  bool _isDiscovering = false;
  
  @override
  void initState() {
    super.initState();
    _controller.text = SharedPreferencesUtil().backendUrl ?? 'http://localhost:8000';
  }
  
  Future<void> _discoverBackend() async {
    setState(() => _isDiscovering = true);
    
    final discovered = await BackendDiscovery.discoverBackend();
    if (discovered != null) {
      _controller.text = discovered;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Found local backend at $discovered')),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('No local backend found')),
      );
    }
    
    setState(() => _isDiscovering = false);
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Backend Settings')),
      body: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _controller,
              decoration: InputDecoration(
                labelText: 'Backend URL',
                hintText: 'http://localhost:8000',
              ),
            ),
            SizedBox(height: 16),
            ElevatedButton(
              onPressed: _isDiscovering ? null : _discoverBackend,
              child: Text(_isDiscovering ? 'Discovering...' : 'Auto-discover'),
            ),
            SizedBox(height: 8),
            ElevatedButton(
              onPressed: () {
                SharedPreferencesUtil().backendUrl = _controller.text;
                Navigator.pop(context);
              },
              child: Text('Save'),
            ),
          ],
        ),
      ),
    );
  }
}
```

## Performance Considerations

### Model Selection

| Model Type | Recommended | Use Case | Hardware |
|------------|-------------|----------|----------|
| LLM | Llama 3 8B | General conversation | 16GB RAM |
| LLM | Mistral 7B | Fast responses | 8GB RAM |
| STT | Whisper Base | Good accuracy | CPU |
| STT | Whisper Tiny | Fast processing | CPU |
| Embeddings | nomic-embed-text | Semantic search | CPU |

### Optimization Tips

1. **GPU Acceleration**: Use NVIDIA GPU for Ollama when available
2. **Model Quantization**: Use Q4_K_M quantized models for better performance
3. **Caching**: Implement aggressive caching for embeddings
4. **Batch Processing**: Process multiple requests in batches when possible

## Testing

### Integration Tests

```python
# tests/test_ollama_integration.py
import pytest
from backend.services.ollama_service import OllamaService

@pytest.mark.asyncio
async def test_chat_completion():
    service = OllamaService()
    response = await service.chat_completion(
        messages=[{"role": "user", "content": "Hello"}],
        model="llama3"
    )
    assert "message" in response
    assert response["message"]["content"]

@pytest.mark.asyncio
async def test_embeddings():
    service = OllamaService()
    embedding = await service.embeddings("Test text")
    assert isinstance(embedding, list)
    assert len(embedding) > 0
```

## Migration Checklist

- [ ] Set up Ollama service
- [ ] Implement LLM provider abstraction
- [ ] Update memory processing endpoints
- [ ] Integrate Whisper.cpp for STT
- [ ] Update vector database to use local embeddings
- [ ] Create Docker Compose configuration
- [ ] Update Flutter app backend discovery
- [ ] Add backend configuration UI
- [ ] Test end-to-end flow
- [ ] Document configuration options
- [ ] Create model download scripts
- [ ] Performance benchmarking

## Next Steps

1. Start with basic Ollama integration
2. Test with simple chat completion
3. Gradually migrate each AI service
4. Optimize for performance
5. Add fallback mechanisms