# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Omi (formerly Friend) is an open-source AI wearable ecosystem that captures conversations, provides summaries, and executes actions. It consists of:
- Flutter mobile app (iOS/Android/desktop)
- Python FastAPI backend deployed on Modal
- Hardware firmware (Omi device and OmiGlass)
- Web frontend (Next.js)
- Developer SDKs and plugin system

## Key Commands

### Mobile App Development (`/app`)
```bash
# Setup
bash setup.sh ios    # or android

# Development
flutter run --flavor dev
flutter build ios --flavor dev --release
flutter build android --flavor dev --release
flutter pub get
dart run build_runner build
```

### Backend Development (`/backend`)
```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt

# Run server
uvicorn main:app --reload --env-file .env

# External access
ngrok http --domain=example.ngrok-free.app 8000
```

### Web Frontend (`/web/frontend`)
```bash
npm install
npm run dev      # Development server
npm run build    # Production build
npm run lint     # Linting
npm run lint:fix # Fix linting issues
```

### Firmware Development (`/omi/firmware`)
```bash
# Build with Docker (recommended)
./scripts/build-docker.sh
./scripts/build-docker.sh --clean  # Clean build

# Flash to device
./flash.sh  # For devkit
```

### Testing
```bash
# Python (backend, MCP)
pytest

# Flutter app
flutter test
```

## Architecture Overview

### Component Communication Flow
```
Mobile App <--WebSocket--> Backend API <---> External Services
    |                          |                    |
    v                          v                    v
BLE Device              Firestore/Redis        AI Services
                                              (OpenAI, Deepgram)
```

### Key Architectural Decisions

1. **State Management**: Flutter app uses Provider pattern for state management across authentication, conversations, memories, and device connectivity.

2. **Real-time Communication**: WebSocket-based audio streaming protocol with configurable codecs (PCM8, Opus) and multi-language STT support.

3. **Database Strategy**: 
   - Firestore for persistent data (users, memories, conversations)
   - Redis for caching and real-time data
   - Vector database for semantic search

4. **Plugin Architecture**: Webhook-based integration system allows third-party apps to extend functionality through standardized endpoints.

5. **Hardware Protocol**: BLE communication using custom service UUID `19B10000-E8F2-537E-4F6C-D104768A1214` for audio streaming and device control.

### API Router Structure
Backend uses modular routers under `/backend/routers/`:
- `transcribe.py` - WebSocket audio streaming and transcription
- `memories.py` - Memory CRUD operations
- `apps.py` - Plugin/app integrations
- `chat.py` - AI chat interactions
- `notifications.py` - Push notification management

### Mobile App Provider Architecture
Key providers in `/app/lib/providers/`:
- `capture_provider.dart` - Audio capture and processing
- `device_provider.dart` - BLE device management
- `websocket_provider.dart` - Real-time communication
- `memory_provider.dart` - Memory state management

## Development Guidelines

1. **Authentication**: All API endpoints require Firebase authentication unless explicitly public. Check authentication middleware in `backend/middleware/auth.py`.

2. **WebSocket Protocol**: When modifying audio streaming, ensure compatibility with existing codec support and maintain backward compatibility with deployed devices.

3. **BLE Communication**: Device firmware and mobile app must maintain protocol compatibility. Check `friend_device_base.dart` for protocol implementation.

4. **Memory Processing**: Memory creation involves transcription, summarization, and categorization. Changes should maintain the pipeline in `memory_processing.py`.

5. **Plugin Development**: Follow the webhook specification in `backend/routers/apps.py` for new integrations. Plugins receive conversation data and can trigger actions.

## Environment Variables

Key environment variables needed:
- Firebase credentials and configuration
- API keys for AI services (OpenAI, Deepgram, etc.)
- Redis connection strings
- Modal deployment tokens
- Stripe API keys for payments

See component-specific README files for detailed setup instructions.