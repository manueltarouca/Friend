# Product Requirements Document: OMI Privacy-Focused Fork

## Executive Summary

This document outlines the roadmap for creating a privacy-focused fork of the OMI (Friend) project that eliminates all telemetry, third-party API dependencies, and cloud services in favor of local, self-hosted alternatives.

## Project Vision

Create a fully open-source, privacy-respecting AI wearable ecosystem where:
- All data processing happens locally on user-controlled hardware
- No telemetry or analytics data leaves the device ecosystem
- AI models run locally using Ollama or similar tools
- Users maintain complete ownership and control of their conversation data

## Core Principles

1. **Privacy First**: No data leaves the user's control without explicit consent
2. **Local Processing**: All AI and data processing happens on user hardware
3. **Self-Hosted**: Backend services run on user's own infrastructure
4. **Open Source**: All components remain fully open source
5. **No Vendor Lock-in**: Use standard protocols and replaceable components

## Technical Architecture Changes

### Current Architecture
```
Mobile App → Firebase Auth → Modal Backend → OpenAI/Deepgram
     ↓            ↓              ↓              ↓
BLE Device   Analytics      Firestore    Cloud Services
```

### Target Architecture
```
Mobile App → Local Auth → Local Backend → Ollama/Whisper
     ↓           ✗             ↓              ↓
BLE Device   No Analytics  Local DB     Local Services
```

## Migration Roadmap

### Phase 1: Foundation (Weeks 1-4)
**Goal**: Remove telemetry and establish local development environment

#### 1.1 Telemetry Removal
- [ ] Remove Firebase Analytics from mobile app
- [ ] Remove Mixpanel tracking from backend
- [ ] Remove all analytics SDKs and dependencies
- [ ] Strip out crash reporting services (Sentry, etc.)
- [ ] Create feature flags for any remaining external services

#### 1.2 Local Backend Setup
- [ ] Create Docker Compose configuration for local services
- [ ] Replace Modal deployment with local FastAPI server
- [ ] Set up local Redis instance
- [ ] Configure local PostgreSQL to replace Firestore
- [ ] Create migration scripts for existing data

#### 1.3 Authentication Replacement
- [ ] Implement local JWT-based authentication
- [ ] Remove Firebase Auth dependencies
- [ ] Create user management API endpoints
- [ ] Build simple web UI for user administration

### Phase 2: AI Localization (Weeks 5-8)
**Goal**: Replace cloud AI services with local alternatives

#### 2.1 LLM Integration
- [ ] Integrate Ollama API for LLM processing
- [ ] Create abstraction layer for model switching
- [ ] Implement fallback for different model sizes
- [ ] Add configuration for model selection
- [ ] Performance optimization for mobile/edge devices

#### 2.2 Speech-to-Text Replacement
- [ ] Integrate OpenAI Whisper for local STT
- [ ] Implement streaming transcription with whisper.cpp
- [ ] Create audio preprocessing pipeline
- [ ] Optimize for real-time performance
- [ ] Add language model configuration

#### 2.3 Memory and Search
- [ ] Replace vector database with local alternative (ChromaDB/Qdrant)
- [ ] Implement local embedding generation
- [ ] Create backup/restore functionality
- [ ] Build memory export features

### Phase 3: Infrastructure Simplification (Weeks 9-12)
**Goal**: Simplify deployment and improve self-hosting experience

#### 3.1 Single Binary Distribution
- [ ] Package backend as single executable
- [ ] Bundle required models and dependencies
- [ ] Create installer scripts for major platforms
- [ ] Implement auto-update mechanism (optional, privacy-respecting)

#### 3.2 Mobile App Modifications
- [ ] Remove all external API calls
- [ ] Implement local backend discovery (mDNS/Bonjour)
- [ ] Add connection settings UI
- [ ] Create offline mode with sync capabilities
- [ ] Build data export/import features

#### 3.3 Hardware Integration
- [ ] Ensure firmware works without cloud services
- [ ] Implement direct BLE to local backend bridge
- [ ] Add firmware update mechanism via local server
- [ ] Create hardware debugging tools

### Phase 4: Privacy Features (Weeks 13-16)
**Goal**: Add privacy-enhancing features

#### 4.1 Data Security
- [ ] Implement end-to-end encryption for stored data
- [ ] Add secure key management
- [ ] Create data retention policies and auto-deletion
- [ ] Build audit logging for data access

#### 4.2 Network Security
- [ ] Add TLS support for all local communications
- [ ] Implement certificate pinning
- [ ] Create VPN/Tor support for any remaining external features
- [ ] Add network isolation options

#### 4.3 User Control
- [ ] Build comprehensive privacy dashboard
- [ ] Add granular permission controls
- [ ] Create data anonymization tools
- [ ] Implement selective sharing features

### Phase 5: Community Features (Weeks 17-20)
**Goal**: Enable privacy-respecting collaboration

#### 5.1 Federated Features
- [ ] Design federated plugin/app system
- [ ] Implement peer-to-peer sync (optional)
- [ ] Create encrypted backup sharing
- [ ] Build privacy-preserving analytics (local only)

#### 5.2 Documentation and Tools
- [ ] Write comprehensive self-hosting guide
- [ ] Create privacy audit documentation
- [ ] Build automated testing for privacy compliance
- [ ] Develop contribution guidelines

## Technical Specifications

### Local AI Stack
```
- LLM: Ollama (supporting multiple models)
  - Recommended: Llama 3, Mistral, Phi-3
  - API: OpenAI-compatible endpoints
  
- STT: Whisper (via whisper.cpp)
  - Models: tiny, base, small, medium
  - Streaming support required
  
- Embeddings: Local sentence-transformers
  - Model: all-MiniLM-L6-v2 or similar
  
- Vector DB: ChromaDB or Qdrant
  - Local persistence
  - Efficient similarity search
```

### Minimum Hardware Requirements
```
Desktop/Server:
- CPU: 4+ cores recommended
- RAM: 8GB minimum, 16GB recommended
- Storage: 50GB for models and data
- GPU: Optional but recommended for larger models

Mobile:
- Existing OMI hardware unchanged
- Mobile app size increase due to local models
```

### Migration Tools
```
- Data export from Firebase
- User migration scripts
- Model download automation
- Configuration migration
```

## Success Metrics

1. **Privacy Compliance**
   - Zero external API calls (verified by network monitoring)
   - All data stored locally
   - No telemetry beacons

2. **Performance**
   - STT latency < 2 seconds
   - LLM response time < 5 seconds
   - Memory search < 500ms

3. **Usability**
   - Setup time < 30 minutes
   - No degradation in core features
   - Offline functionality

## Risks and Mitigations

### Risk 1: Performance Degradation
- **Mitigation**: Offer multiple model sizes, implement caching, optimize algorithms

### Risk 2: Increased Complexity
- **Mitigation**: Create one-click installers, comprehensive documentation

### Risk 3: Hardware Requirements
- **Mitigation**: Support range of models, cloud-optional hybrid mode

### Risk 4: Community Fragmentation
- **Mitigation**: Maintain compatibility where possible, clear communication

## Next Steps

1. **Community Engagement**
   - Announce fork intentions
   - Gather feedback on priorities
   - Recruit contributors

2. **Technical Prototype**
   - Proof of concept with Ollama integration
   - Performance benchmarking
   - Security audit

3. **Project Setup**
   - Create new repository
   - Set up CI/CD pipelines
   - Establish communication channels

## Appendix: Alternative Technologies

### LLM Alternatives
- LlamaCPP
- LocalAI
- Text Generation WebUI

### STT Alternatives
- Vosk
- SpeechRecognition
- PocketSphinx

### Database Alternatives
- SQLite + Vector extensions
- DuckDB
- Milvus Lite

---

*This is a living document and will be updated as the project evolves.*