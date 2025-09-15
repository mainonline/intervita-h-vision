# Technology Stack

## Core Framework
- **LiveKit Agents**: Real-time communication framework for voice/video agents
- **Python 3.11**: Primary runtime environment
- **Docker**: Containerized deployment
- **Fly.io**: Cloud hosting platform

## Key Dependencies
- **livekit-agents**: Core agent framework (>=0.12.17)
- **livekit-plugins-openai**: OpenAI integration for LLM (>=0.11.2)
- **livekit-plugins-deepgram**: Speech-to-text and text-to-speech (>=0.7.0)
- **livekit-plugins-cartesia**: Alternative TTS option (>=0.4.10)
- **livekit-plugins-silero**: Voice activity detection (>=0.7.5)
- **livekit-plugins-turn-detector**: Turn detection model (>=0.4.3)
- **livekit-plugins-noise-cancellation**: Background noise filtering (>=0.2.0)
- **aiohttp**: HTTP server for health checks (==3.11.16)
- **python-dotenv**: Environment variable management (~=1.0)

## AI Models
- **LLM**: OpenAI GPT-4o-mini for conversation
- **STT**: Deepgram for speech recognition
- **TTS**: Deepgram Aura Luna model (32kHz sample rate)
- **VAD**: Silero voice activity detection
- **Turn Detection**: LiveKit's transformer-based EOUModel

## Common Commands

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run agent locally
python agent.py start

# Download required models
python agent.py download-files

# Run health check server
python healthcheck.py
```

### Docker
```bash
# Build image
docker build -t intervita-vision .

# Run container
docker run -p 8081:8081 intervita-vision
```

### Deployment
```bash
# Deploy to Fly.io
fly deploy

# Check app status
fly status

# View logs
fly logs
```

## Environment Variables
- Standard LiveKit environment variables for API keys and configuration
- Uses `.env` file for local development
- Health check endpoint exposed on port 8081