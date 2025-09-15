# Project Structure

## Root Files
- **agent.py**: Main application entry point and agent logic
- **healthcheck.py**: Simple HTTP health check server for monitoring
- **requirements.txt**: Python dependencies specification
- **Dockerfile**: Container build configuration
- **fly.toml**: Fly.io deployment configuration
- **.dockerignore**: Files to exclude from Docker build context
- **.gitignore**: Git version control exclusions

## Key Directories
- **.kiro/**: Kiro IDE configuration and steering rules
- **.vscode/**: VS Code editor configuration

## Code Organization

### agent.py Structure
The main agent file follows a clear functional organization:

1. **Imports and Setup**: All dependencies and logging configuration
2. **Helper Functions**: 
   - `get_greeting_message()`: Random greeting generation
   - `get_role_instructions()`: Core interviewer prompt
   - `create_interviewer_prompt()`: Full prompt assembly
3. **Main Entry Point**: `entrypoint(ctx)` function containing:
   - Room connection and participant handling
   - Metadata parsing (resume, questions, job context)
   - Video capture and processing logic
   - RPC method registration
   - Agent configuration and callbacks
   - Event handlers for transcripts and room events

### Configuration Files
- **fly.toml**: Comprehensive deployment config with autoscaling, health checks, and resource allocation
- **Dockerfile**: Multi-stage build with security best practices (non-root user)
- **requirements.txt**: Pinned versions for reproducible builds

## Coding Conventions
- Use async/await for all I/O operations
- Comprehensive error handling with try/catch blocks
- Structured logging with contextual information
- Clear separation of concerns between functions
- Type hints for function parameters and returns
- Descriptive variable names and function documentation

## Deployment Architecture
- Single-file application design for simplicity
- Health check endpoint on port 8081
- Graceful shutdown handling with 60s timeout
- Blue-green deployment strategy
- Auto-scaling based on CPU/memory utilization
- Comprehensive monitoring and metrics collection