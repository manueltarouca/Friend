#!/bin/bash
# Setup script for OMI Privacy Fork - Local Deployment

set -e

echo "🚀 OMI Privacy Fork - Local Setup"
echo "================================="
echo

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check dependencies
check_dependency() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}✗ $1 is not installed${NC}"
        return 1
    else
        echo -e "${GREEN}✓ $1 is installed${NC}"
        return 0
    fi
}

echo "Checking dependencies..."
DEPS_OK=true
check_dependency "docker" || DEPS_OK=false
check_dependency "docker-compose" || DEPS_OK=false
check_dependency "curl" || DEPS_OK=false

if [ "$DEPS_OK" = false ]; then
    echo -e "\n${RED}Please install missing dependencies before continuing.${NC}"
    exit 1
fi

# Create necessary directories
echo -e "\nCreating directories..."
mkdir -p models/whisper
mkdir -p models/ollama
mkdir -p nginx/ssl
mkdir -p backend/logs

# Start services
echo -e "\n${YELLOW}Starting Docker services...${NC}"
docker-compose -f docker-compose.local.yml up -d

# Wait for Ollama to be ready
echo -e "\n${YELLOW}Waiting for Ollama to start...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ollama is ready${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

# Pull Ollama models
echo -e "\n${YELLOW}Pulling Ollama models...${NC}"
echo "This may take several minutes depending on your internet connection..."

# Function to pull model with retry
pull_model() {
    local model=$1
    local max_retries=3
    local retry=0
    
    while [ $retry -lt $max_retries ]; do
        echo -e "Pulling $model (attempt $((retry+1))/$max_retries)..."
        if docker exec omi-ollama ollama pull $model; then
            echo -e "${GREEN}✓ Successfully pulled $model${NC}"
            return 0
        else
            retry=$((retry+1))
            if [ $retry -lt $max_retries ]; then
                echo -e "${YELLOW}Retrying in 5 seconds...${NC}"
                sleep 5
            fi
        fi
    done
    
    echo -e "${RED}✗ Failed to pull $model after $max_retries attempts${NC}"
    return 1
}

# Pull models
pull_model "llama3"
pull_model "nomic-embed-text"

# Optional: Pull additional models
echo -e "\n${YELLOW}Would you like to pull additional models? (y/N)${NC}"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "Available models:"
    echo "1. codellama (for code-related tasks)"
    echo "2. mistral (fast, general purpose)"
    echo "3. phi3 (small, efficient)"
    echo "4. llama3:70b (large, more capable)"
    echo -e "\nEnter model numbers separated by spaces (e.g., '1 2'):"
    read -r models
    
    if [[ $models == *"1"* ]]; then pull_model "codellama"; fi
    if [[ $models == *"2"* ]]; then pull_model "mistral"; fi
    if [[ $models == *"3"* ]]; then pull_model "phi3"; fi
    if [[ $models == *"4"* ]]; then pull_model "llama3:70b"; fi
fi

# Download Whisper models
echo -e "\n${YELLOW}Downloading Whisper models...${NC}"
if [ ! -f "models/whisper/ggml-base.bin" ]; then
    echo "Downloading Whisper base model..."
    curl -L https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin \
         -o models/whisper/ggml-base.bin \
         --progress-bar
    echo -e "${GREEN}✓ Whisper model downloaded${NC}"
else
    echo -e "${GREEN}✓ Whisper model already exists${NC}"
fi

# Check service health
echo -e "\n${YELLOW}Checking service health...${NC}"
sleep 5

check_service() {
    local service=$1
    local port=$2
    local endpoint=$3
    
    if curl -s http://localhost:$port$endpoint > /dev/null 2>&1; then
        echo -e "${GREEN}✓ $service is healthy${NC}"
        return 0
    else
        echo -e "${RED}✗ $service is not responding${NC}"
        return 1
    fi
}

check_service "Ollama" 11434 "/api/tags"
check_service "Backend API" 8000 "/docs"
check_service "Redis" 6379 ""
check_service "ChromaDB" 8001 "/api/v1/heartbeat"

# Create .env file if it doesn't exist
if [ ! -f "backend/.env" ]; then
    echo -e "\n${YELLOW}Creating backend .env file...${NC}"
    cat > backend/.env << EOF
# Local deployment configuration
LLM_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Database
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://omi:omipassword@localhost:5432/omi

# ChromaDB
CHROMA_HOST=http://localhost:8001

# Disable telemetry
DISABLE_TELEMETRY=true
DISABLE_ANALYTICS=true

# Environment
ENVIRONMENT=local
DEBUG=true
EOF
    echo -e "${GREEN}✓ .env file created${NC}"
fi

# Show status
echo -e "\n${GREEN}=================================${NC}"
echo -e "${GREEN}✅ Local setup complete!${NC}"
echo -e "${GREEN}=================================${NC}"
echo
echo "Services running:"
echo "- Ollama (LLM): http://localhost:11434"
echo "- Backend API: http://localhost:8000"
echo "- API Docs: http://localhost:8000/docs"
echo "- ChromaDB: http://localhost:8001"
echo "- Redis: localhost:6379"
echo "- PostgreSQL: localhost:5432"
echo
echo "To view logs:"
echo "  docker-compose -f docker-compose.local.yml logs -f"
echo
echo "To stop services:"
echo "  docker-compose -f docker-compose.local.yml down"
echo
echo "To test the local chat API:"
echo "  curl -X POST http://localhost:8000/v1/chat/local/health"
echo
echo -e "${YELLOW}Note: Update your OMI app settings to point to http://localhost:8000${NC}"