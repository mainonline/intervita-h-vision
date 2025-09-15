import logging
import json
from typing import Optional
import asyncio
import time

from dotenv import load_dotenv
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
    metrics,
    transcription,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import (
    deepgram,
    noise_cancellation,
    silero,
    turn_detector,
    openai,
)


from livekit import rtc

from livekit.agents.llm import ChatMessage, ChatImage
from typing import Dict, Any, List
import random
load_dotenv(dotenv_path=".env")
logger = logging.getLogger("vision-voice-agent")


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


def get_greeting_message() -> str:
    """Return a random two-sentence greeting with Evita introducing herself, no time reference."""

    agent_name = "Evita"
    greetings = [
        f"Hey there, I’m {agent_name}, thrilled to chat about your future. Let’s dive in.",
        f"Hi, I’m {agent_name}, great to meet you for this interview. Ready to get started?",
        f"Hello, I’m {agent_name}, excited to talk about your skills today. Here we go.",
        f"Hey, I’m {agent_name}, glad to connect with you right now. Let’s make it quick and sharp.",
        f"Hi there, I’m {agent_name}, here to see what you’re all about. Settle in, we’re off.",
        f"Hello, I’m {agent_name}, happy to jump into this with you. Let’s hit the ground running.",
        f"Hey, I’m {agent_name}, pumped to talk career moves today. Buckle up, we’re starting.",
        f"Hi, I’m {agent_name}, stoked to chat with you right now. Let’s roll.",
        f"Hello there, I’m {agent_name}, loving that we’re doing this today. Time to shine.",
        f"Hey, I’m {agent_name}, awesome to meet you wherever you’re at. Let’s do this."
    ]
    return random.choice(greetings)


def get_role_instructions(max_interview_minutes: int) -> str:
    """Return the role and time constraint instructions."""
    return (
        "You are Evita, an experienced interviewer at Intervita.ai. Your role adapts to the candidate's field—HR, department head, or hiring manager—as needed. You conduct real-time voice and video interviews, observing candidates via their camera and responding naturally.\n\n"
        
        "**YOUR ROLE:**\n"
        "Interview candidates based on their resume, optional job context, and provided questions. Assess their skills, experience, and fit for the role they're targeting. Maintain a direct, slightly casual yet professional tone, reflecting the time-limited nature of the session.\n\n"
        
        f"**VERY IMPORTANT NOTICE: TIME CONSTRAINT**\n"
        f"**You have a maximum of {max_interview_minutes} minutes to complete this interview.** "
        f"At the start, clearly inform the candidate: 'We have only {max_interview_minutes} minutes to complete the interview, so let's make it efficient.' "
        "Stay on track, prioritize key questions, and avoid tangents. Pace yourself to cover essential topics and conclude within the time limit. "
        "If time is running short, remind them: 'We've got just a few minutes left of our {max_interview_minutes}-minute session—let's wrap up.' "
        "End efficiently with a final question or summary if needed."
    )

def get_candidate_info(resume_data: Dict[str, Any], job_context: Optional[str]) -> str:
    """Return candidate resume and job context details."""
    return (
        f"**CANDIDATE RESUME:**\n{json.dumps(resume_data, indent=2) if resume_data else 'No resume data provided.'}\n\n"
        f"**JOB CONTEXT (Optional):**\n{job_context if job_context else 'No job context provided.'}"
    )

def get_questions_section(questions: List[str]) -> str:
    """Return provided questions and usage instructions."""
    return (
        f"**PROVIDED QUESTIONS:**\n{json.dumps(questions, indent=2) if questions else 'No specific questions provided.'}\n"
        "Use these questions as a starting point, adapting based on the candidate's answers."
    )

def get_interview_approach() -> str:
    """Return the interview approach and sample questions."""
    return (
        "**INTERVIEW APPROACH:**\n"
        "1. Begin with a brief, casual introduction, referencing something visual from their camera.\n"
        "2. Highlight a specific detail from their resume (if available) to show preparation.\n"
        "3. Ask the provided questions, weaving in resume and job context details where relevant.\n"
        "4. Target their answers with follow-up questions (e.g., 'You mentioned X—can you elaborate?' or 'How did that impact Y?').\n"
        "5. Mix in challenging questions to test reasoning under pressure.\n"
        "6. Challenge vague answers—demand specific examples.\n"
        "7. Probe claimed expertise with follow-ups.\n"
        "8. Show subtle skepticism when warranted—make them justify their fit.\n"
        "9. Allow candidate questions, but steer the conversation and respect the time limit.\n\n"
        
        "**SAMPLE QUESTIONS (Supplement as Needed):**\n"
        "- 'Walk me through your professional background.' (Interrupt if they ramble.)\n"
        "- 'Why are you leaving your current role?' (Watch for negativity.)\n"
        "- 'What's your biggest weakness, per your colleagues?' (Push past clichés.)\n"
        "- 'Where do you see yourself in a few years?' (Assess ambition.)\n"
        "- 'Describe a major work challenge you faced.' (Evaluate problem-solving.)\n"
        "- 'How do you handle disagreements with a manager?' (Test conflict skills.)\n"
        "- 'What sets you apart from others?' (Gauge self-awareness.)\n"
        "- 'What do you know about our company?' (Check preparation.)\n"
        "- 'How do you manage stress or tight deadlines?' (Seek examples.)\n"
        "- 'Explain [resume skill] to a beginner.' (Verify expertise.)\n"
        "- 'You spent X years at [company]—why'd you leave?'\n"
        "- 'What were you doing during this resume gap?'"
    )

def get_tone_and_video_instructions() -> str:
    """Return tone, style, and video interaction instructions."""
    return (
        "**TONE AND STYLE:**\n"
        "- Direct and slightly skeptical—candidates must prove themselves.\n"
        "- Casual yet professional, avoiding overly friendly chatter.\n"
        "- Concise and natural, like a busy interviewer.\n"
        "- Acknowledge potential nervousness but maintain real-interview pressure.\n"
        "- Interrupt rehearsed or vague responses for clarity.\n"
        "- If data is missing, adapt with broader questions.\n\n"
        
        "**VIDEO INTERACTION (CRITICAL):**\n"
        "- You see the candidate via their camera—reference visual cues every 3-4 exchanges.\n"
        "- Examples: 'You're smiling about that project—why's it special?' | 'That's a cool bookshelf behind you—what's on it?' | 'You're animated about this—tell me more.' | 'Nice professional attire today.'\n"
        "- Keep references natural and relevant, not forced.\n"
        "- If they're out of frame, say: 'I'd like to see you for this next question.'\n"
        "- Start with a visual observation: 'I see you've got a great setup there—let's dive in.'\n"
        "- Act human—never mention AI or tech details."
    )

def create_interviewer_prompt(
    resume_data: Dict[str, Any],
    questions: List[str] = [],
    max_interview_minutes: int = 10,
    job_context: Optional[str] = None,
) -> str:
    """Create the full interviewer prompt."""
    return "\n\n".join([
        get_role_instructions(max_interview_minutes),
        get_candidate_info(resume_data, job_context),
        get_questions_section(questions),
        get_interview_approach(),
        get_tone_and_video_instructions(),
        "**GUIDANCE:**\n"
        "Prioritize provided questions, tailoring them with resume and job context details. Actively listen to answers and ask follow-ups (e.g., 'That's interesting—how did you handle Z?' or 'What was the outcome?'). Balance visual feedback with substantive discussion, staying within the time limit."
    ])
async def entrypoint(ctx: JobContext):

    logger.info(f"connecting to room {ctx.room.name}")
    # Update subscription to include video
    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    # Wait for the first participant to connect - we need to do this first to get metadata
    participant = await ctx.wait_for_participant()
    
    # Parse the participant metadata (resume data)
    resume_data = {}
    questions = []
    job_context = ""
    max_interview_minutes = 10
    try:
        if participant.metadata:
            # Parse the JSON string once
            parsed_metadata = json.loads(participant.metadata)
            
            # Access the fields directly - they're already parsed
            resume_data = parsed_metadata.get('resume_data', {})
            questions = parsed_metadata.get('questions', [])
            max_interview_minutes = parsed_metadata.get('max_interview_minutes', 10)
            job_context = parsed_metadata.get('job_context', '')

    except json.JSONDecodeError:
        logger.error(f"Failed to parse participant metadata as JSON: {participant.metadata}")
    except Exception as e:
        logger.error(f"Error processing participant metadata: {str(e)}")
    
    # Log the parsed metadata
    logger.info(f"participant metadata: {participant.metadata}")
    
    # Create the interviewer prompt, incorporating resume data if available
    prompt = create_interviewer_prompt(resume_data, questions, max_interview_minutes, job_context)
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=prompt
    )


    logger.info(f"starting interview for candidate {participant.identity}")
    
    # Create a forwarder for user transcriptions
    # We will set up the forwarder after we get audio tracks
    stt_forwarder = None
    latest_video_track: Optional[rtc.VideoTrack] = None

     # Function to capture image from video track
    async def get_video_track(room: rtc.Room):
        """Find and return the first available remote video track in the room."""
        for participant_id, participant in room.remote_participants.items():
            for track_id, track_publication in participant.track_publications.items():
                if track_publication.track and isinstance(
                    track_publication.track, rtc.RemoteVideoTrack
                ):
                    logger.info(
                        f"Found video track {track_publication.track.sid} "
                        f"from participant {participant_id}"
                    )
                    return track_publication.track
        raise ValueError("No remote video track found in the room")
    
    async def get_latest_image(room: rtc.Room):
        """Capture and return a single frame from the video track if available."""
        video_stream = None
        try:
            # First check if we can get a video track
            try:
                video_track = await get_video_track(room)
            except ValueError:
                # No video track found - this is normal when video is off
                logger.debug("No video track available")
                return None
            
            if video_track is None:
                return None
            # Create video stream with timeout to prevent hanging
            video_stream = rtc.VideoStream(video_track)
            
            # Use asyncio.wait_for to add a timeout
            try:
                # Set a reasonable timeout (1 second)
                async def get_first_frame():
                    async for event in video_stream:
                        logger.debug("Captured latest video frame")
                        return event.frame
                    return None
                    
                return await asyncio.wait_for(get_first_frame(), timeout=1.0)
            except asyncio.TimeoutError:
                logger.warning("Timeout while waiting for video frame - camera might be off")
                return None
            
        except Exception as e:
            logger.warning(f"Failed to get latest image: {e}")
            return None
        finally:
            if video_stream:
                await video_stream.aclose()

    async def before_llm_cb(assistant: VoicePipelineAgent, chat_ctx: llm.ChatContext):
        """
        Callback that runs right before the LLM generates a response.
        Captures the current video frame and adds it to the conversation context.
        If video is unavailable, continues without adding image content.
        """
        try:
            latest_image = await get_latest_image(ctx.room)
            if latest_image:
                # Add the image to the conversation context
                image_content = [ChatImage(image=latest_image)]
                chat_ctx.messages.append(ChatMessage(role="user", content=image_content))
                logger.debug("Added latest frame to conversation context")
            else:
                logger.debug("No video frame available, continuing without vision")
        except Exception as e:
            # Catch any errors during video capture and allow the agent to continue
            logger.warning(f"Error capturing video frame: {e}. Continuing without vision.")
    
    # Flag to track conversation state
    conversation_ending = False

    # Register RPC methods with better error handling
    try:
        @ctx.room.local_participant.register_rpc_method("end_conversation")
        async def handle_end_conversation(data: rtc.RpcInvocationData):
            """Allow frontend to explicitly end the conversation"""
            nonlocal conversation_ending
            logger.info(f"Received end_conversation request from {data.caller_identity}")
            conversation_ending = True
            
            # Say goodbye before disconnecting
            try:
                await agent.say("Thank you for the interview today. Goodbye!")
            except Exception as e:
                logger.error(f"Error saying goodbye: {str(e)}")
            
            # Return response before disconnecting
            # This ensures the client gets a response before the agent disconnects
            response = "Conversation ended successfully"
            
            # Schedule disconnect to happen after returning the response
            async def disconnect_after_delay():
                try:
                    await asyncio.sleep(2)
                    logger.info("Disconnecting from room due to end_conversation RPC")
                    await ctx.room.disconnect()
                except Exception as e:
                    logger.error(f"Error during disconnect: {str(e)}")
                
            asyncio.create_task(disconnect_after_delay())
            
            return response
        
        # Add a simple ping method for testing RPC connectivity
        @ctx.room.local_participant.register_rpc_method("ping")
        async def handle_ping(data: rtc.RpcInvocationData):
            """Simple ping method to check if RPC is working"""
            logger.info(f"Received ping from {data.caller_identity}")
            return f"Pong! Agent is alive and received: {data.payload}"
        
        logger.info("Successfully registered RPC methods")
    except Exception as e:
        logger.error(f"Failed to register RPC methods: {str(e)}")

    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=deepgram.STT(),
        llm=openai.LLM(model="gpt-4o-mini"),
        # llm=llm_plugin.LLM.with_groq(model="grok-2-vision-1212", temperature=0.8),
        # tts=cartesia.TTS(),
        tts=deepgram.tts.TTS(
            model="aura-luna-en",
            sample_rate=32000,
            
        ),
        # use LiveKit's transformer-based turn detector
        turn_detector=turn_detector.EOUModel(),
        # minimum delay for endpointing, used when turn detector believes the user is done with their turn
        min_endpointing_delay=0.5,
        # maximum delay for endpointing, used when turn detector does not believe the user is done with their turn
        max_endpointing_delay=5.0,
        # enable background voice & noise cancellation, powered by Krisp
        # included at no additional cost with LiveKit Cloud
        noise_cancellation=noise_cancellation.BVC(),
        chat_ctx=initial_ctx,
        before_llm_cb=before_llm_cb,
    )

    usage_collector = metrics.UsageCollector()

    @agent.on("metrics_collected")
    def on_metrics_collected(agent_metrics: metrics.AgentMetrics):
        metrics.log_metrics(agent_metrics)
        usage_collector.collect(agent_metrics)
    
    
    # Set up the forwarder when we get audio tracks
    @ctx.room.on("track_subscribed")
    def on_track_subscribed(track, publication, remote_participant):
        nonlocal stt_forwarder, latest_video_track
        
        if remote_participant.identity != participant.identity:
            return
            
        if track.kind == 'audio':
            # Now we have the participant's audio track, we can set up the forwarder
            stt_forwarder = transcription.STTSegmentsForwarder(
                room=ctx.room,
                participant=remote_participant,
                track=track
            )
            
            # Configure the agent to use this forwarder
            agent.transcript_forwarder = stt_forwarder
            logger.info(f"Set up transcript forwarding for {remote_participant.identity}")
        
        elif track.kind == 'video':
            # Store the latest video track
            latest_video_track = track
            logger.info(f"Subscribed to video from {remote_participant.identity}")
    
    # Enhanced transcript monitoring for user goodbyes
    @agent.on("transcript")
    def on_transcript(transcript):
        """Monitor user transcripts for goodbye indicators with more cases"""
        nonlocal conversation_ending
        
        if conversation_ending:
            return  # Already ending, no need to check
        
        # Check for goodbye phrases in user transcript
        lower_text = transcript.text.lower()
        
        # Expanded user goodbye indicators
        user_goodbye_indicators = [
            # Standard goodbyes
            "goodbye", "bye", "farewell", "see you", 
            
            # Direct ending statements
            "thank you for your time", "end the interview", "that's all",
            "need to go", "have to leave", "conclude", "finish",
            
            # Implicit endings
            "appreciate the opportunity", "look forward to hearing",
            "hope to hear from you", "next steps", "follow up",
            
            # Time constraints
            "running out of time", "out of time", "another appointment", 
            "getting late", "need to run", "have to run",
            
            # Questions about next steps
            "when will i hear back", "next in the process", 
            "follow up process", "hear about the position"
        ]
        
        # Strong indicators that directly state ending
        strong_ending_phrases = [
            "i need to end now",
            "let's end the interview",
            "i have to go now",
            "that's all i have",
            "thank you for interviewing me",
            "i really need to go"
        ]
        
        # Strong match if we find a clear ending phrase
        strong_match = any(phrase in lower_text for phrase in strong_ending_phrases)
        # Weaker match if we find individual goodbye indicators
        weak_match = any(indicator in lower_text for indicator in user_goodbye_indicators)
        
        if strong_match:
            logger.info(f"User explicitly ended conversation: '{transcript.text}'")
            conversation_ending = True
            
            # Respond with a quick goodbye
            async def say_goodbye_and_disconnect():
                try:
                    await agent.say("Thank you for your time today. Goodbye!")
                    await asyncio.sleep(3)
                    logger.info("Disconnecting room after user explicitly ended conversation")
                    await ctx.room.disconnect()
                except Exception as e:
                    logger.error(f"Error during goodbye response: {e}")
                
            asyncio.create_task(say_goodbye_and_disconnect())
        elif weak_match:
            logger.info(f"User potentially indicating conversation end: '{transcript.text}'")
            # Don't set conversation_ending here - let the LLM respond first

    # Add silence detection for natural conversation ending
    last_interaction_time = time.time()
    silence_check_interval = 30  # seconds
    max_silence_duration = 120  # 2 minutes of silence triggers ending

    async def monitor_silence():
        """Monitor for prolonged silence which might indicate the conversation ended naturally"""
        nonlocal last_interaction_time, conversation_ending
        
        while True:
            await asyncio.sleep(silence_check_interval)
            
            if conversation_ending:
                return  # Already ending, stop monitoring
            
            current_time = time.time()
            silence_duration = current_time - last_interaction_time
            
            if silence_duration > max_silence_duration:
                logger.info(f"Detected prolonged silence ({silence_duration:.1f} seconds), ending conversation")
                conversation_ending = True
                
                try:
                    # Check if the user is still there
                    await agent.say("It seems we've been silent for a while. Is there anything else you'd like to discuss, or shall we conclude the interview?")
                    
                    # Give the user a chance to respond
                    await asyncio.sleep(15)
                    
                    # If still silent, disconnect
                    if time.time() - last_interaction_time > max_silence_duration:
                        logger.info("Still silent after prompt, disconnecting")
                        await agent.say("Since I haven't heard back, I'll end our interview here. Thank you for your time today.")
                        await asyncio.sleep(5)
                        await ctx.room.disconnect()
                except Exception as e:
                    logger.error(f"Error handling silence detection: {e}")
                    await ctx.room.disconnect()

    # Update interaction timestamps for silence detection
    @agent.on("user_started_speaking")
    def on_user_started_speaking():
        nonlocal last_interaction_time
        last_interaction_time = time.time()

    @agent.on("agent_started_speaking")
    def on_agent_started_speaking():
        nonlocal last_interaction_time
        last_interaction_time = time.time()

    # Start the silence monitor
    asyncio.create_task(monitor_silence())

    # Monitor room state for unexpected disconnections
    @ctx.room.on("disconnected")
    def on_room_disconnected():
        logger.info("Room disconnected event received")
    
    @ctx.room.on("reconnecting") 
    def on_room_reconnecting():
        logger.info("Room reconnecting event received")
        nonlocal last_interaction_time
        # Reset interaction time during reconnections to avoid premature ending
        last_interaction_time = time.time()

    agent.start(ctx.room, participant)

    # Capture the candidate's image before greeting

   
    
    # Base greeting
    greeting = get_greeting_message()
    
    # if resume_data.get('name'):
    #     greeting += f", nice to meet you {resume_data.get('name')}"
    
    # else:
    #     # Fallback if no image is available
    #     greeting += "! How's your day going?"
    
    # Start with a greeting that shows the agent can see the candidate
    await agent.say(greeting, allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )

