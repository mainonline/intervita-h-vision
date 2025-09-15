# Intervita Vision - AI Interview Agent

> **Built for the [Code with Kiro Hackathon](https://kiro.devpost.com/)

An AI-powered voice and video interview agent built on LiveKit that conducts real-time interviews with candidates, combining voice interaction with visual analysis through camera feeds.

## Features

- **Real-time Voice & Video**: Conducts live interviews with voice conversation and visual cue recognition
- **Multi-modal AI**: Combines OpenAI GPT-4o-mini with video analysis for comprehensive candidate assessment
- **Dynamic Adaptation**: Adjusts interview flow based on resume data, job context, and provided questions
- **Time Management**: Configurable interview duration with automatic time tracking
- **Natural Conversation**: Handles interruptions, silence detection, and graceful conversation endings
- **Visual Feedback**: References what the agent sees through the candidate's camera
- **RPC Control**: External control via LiveKit RPC methods for programmatic interaction

## Technology Stack

- **LiveKit Agents**: Real-time communication framework
- **Python 3.11**: Core runtime
- **OpenAI GPT-4o-mini**: Conversation AI
- **Deepgram**: Speech-to-text and text-to-speech
- **Silero VAD**: Voice activity detection
- **Docker**: Containerized deployment
- **Fly.io**: Cloud hosting platform

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (for containerized deployment)
- LiveKit account and API credentials
- OpenAI API key
- Deepgram API key

### Local Development

1. **Clone and setup**:

   ```bash
   git clone <repository-url>
   cd intervita-vision
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:

   ```bash
   cp .env.example .env
   # Edit .env with your API keys (see Environment Variables section)
   ```

4. **Download required models**:

   ```bash
   python agent.py download-files
   ```

5. **Run the agent**:

   ```bash
   python agent.py start
   ```

6. **Health check** (optional):
   ```bash
   python healthcheck.py
   ```

### Docker Deployment

1. **Build the image**:

   ```bash
   docker build -t intervita-vision .
   ```

2. **Run container**:
   ```bash
   docker run -p 8081:8081 --env-file .env intervita-vision
   ```

### Fly.io Deployment

1. **Install Fly CLI** and authenticate
2. **Deploy**:

   ```bash
   fly deploy
   ```

3. **Set environment variables**:
   ```bash
   fly secrets set LIVEKIT_URL="your-url"
   fly secrets set LIVEKIT_API_KEY="your-key"
   # ... (set all required variables)
   ```

## Environment Variables

All environment variables should be configured in your `.env` file for local development or as secrets in your deployment platform.

### Required Variables

| Variable             | Description                           | Example                            |
| -------------------- | ------------------------------------- | ---------------------------------- |
| `LIVEKIT_URL`        | LiveKit server WebSocket URL          | `wss://your-project.livekit.cloud` |
| `LIVEKIT_API_KEY`    | LiveKit API key for authentication    | `APIxxxxxxxxxxxxxxxx`              |
| `LIVEKIT_API_SECRET` | LiveKit API secret for authentication | `secretxxxxxxxxxxxxxxxx`           |
| `OPENAI_API_KEY`     | OpenAI API key for GPT-4o-mini        | `sk-xxxxxxxxxxxxxxxx`              |
| `DEEPGRAM_API_KEY`   | Deepgram API key for STT/TTS          | `xxxxxxxxxxxxxxxx`                 |

### Optional Variables

| Variable           | Description                            | Default             |
| ------------------ | -------------------------------------- | ------------------- |
| `CARTESIA_API_KEY` | Cartesia TTS API key (alternative TTS) | Not used by default |
| `XAI_API_KEY`      | xAI API key (for alternative LLM)      | Not used by default |

## Usage

### Interview Configuration

The agent receives configuration through LiveKit participant metadata as JSON:

```json
{
  "resume_data": {
    "name": "John Doe",
    "experience": "5 years in software development",
    "skills": ["Python", "JavaScript", "React"]
  },
  "questions": [
    "Tell me about your experience with Python",
    "Describe a challenging project you worked on"
  ],
  "max_interview_minutes": 15,
  "job_context": "Senior Software Engineer position focusing on backend development"
}
```

### Agent Behavior

**Evita** (the AI interviewer) will:

- Introduce herself with a random, friendly greeting
- Reference visual cues from the candidate's camera
- Ask provided questions while adapting based on responses
- Maintain a professional yet slightly casual tone
- Manage time constraints effectively
- Handle natural conversation flow and endings

### RPC Methods

The agent exposes RPC methods for external control:

- `end_conversation`: Gracefully end the interview
- `ping`: Test connectivity and agent responsiveness

## Architecture

### Core Components

- **agent.py**: Main application with interview logic
- **healthcheck.py**: HTTP health monitoring endpoint
- **VoicePipelineAgent**: LiveKit agent handling voice/video processing
- **Multi-modal Processing**: Combines audio transcription with video frame analysis

### Interview Flow

1. **Connection**: Agent connects to LiveKit room and waits for participant
2. **Setup**: Parses participant metadata for resume/questions/context
3. **Greeting**: Provides personalized introduction with visual reference
4. **Interview**: Conducts structured interview with dynamic follow-ups
5. **Monitoring**: Tracks conversation state and handles natural endings
6. **Conclusion**: Graceful goodbye and disconnection

### Deployment Architecture

- **Autoscaling**: CPU/memory-based scaling (1-4 instances)
- **Health Checks**: TCP and HTTP monitoring on port 8081
- **Blue-Green**: Zero-downtime deployments
- **Resource Limits**: 4GB RAM, 2 CPU cores per instance
- **Graceful Shutdown**: 60-second timeout for clean disconnections

## Development

### Code Structure

The codebase follows these conventions:

- Async/await for all I/O operations
- Comprehensive error handling
- Type hints for better code clarity
- Structured logging with context
- Clear separation of concerns

### Key Functions

- `create_interviewer_prompt()`: Builds dynamic interview prompts
- `get_video_track()`: Captures video frames for visual analysis
- `before_llm_cb()`: Processes video before LLM responses
- `entrypoint()`: Main agent lifecycle management

### Testing

```bash
# Test agent connectivity
python agent.py start

# Test health endpoint
curl http://localhost:8081/health

# Test RPC methods (requires LiveKit client)
# Use LiveKit client to call "ping" method
```

## Monitoring

### Health Checks

- HTTP endpoint: `GET /health` on port 8081
- Returns "OK" when agent is healthy

### Metrics

- LiveKit agent metrics collection
- Usage tracking and performance monitoring
- Automatic logging of conversation events

### Logs

```bash
# Local development
python agent.py start

# Fly.io deployment
fly logs

# Docker container
docker logs <container-id>
```

## Troubleshooting

### Common Issues

1. **Agent won't start**:

   - Check all required environment variables are set
   - Verify LiveKit credentials and URL
   - Ensure Python dependencies are installed

2. **No audio/video**:

   - Verify participant has granted microphone/camera permissions
   - Check LiveKit room configuration
   - Review browser console for WebRTC errors

3. **Interview not adapting**:

   - Ensure participant metadata is properly formatted JSON
   - Check agent logs for parsing errors
   - Verify resume_data structure

4. **Deployment issues**:
   - Check Fly.io secrets are properly set
   - Verify Docker build completes successfully
   - Review deployment logs for errors

### Debug Mode

Enable detailed logging by setting log level in your environment or code:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Follow existing code conventions
2. Add type hints to new functions
3. Include comprehensive error handling
4. Update documentation for new features
5. Test with various interview scenarios

