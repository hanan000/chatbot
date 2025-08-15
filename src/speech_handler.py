import threading
import time
from typing import Optional
import os
from openai import OpenAI
import tempfile
import pygame
import pyaudio
import wave

from src.logger import LOG
from src.utils import get_conf


class SpeechHandler:
    """Handles speech input and output using OpenAI's TTS and STT services.
    Uses OpenAI's text-to-speech API for audio output and Whisper API for
    speech recognition. Audio recording is done via PyAudio and playback
    via pygame.
    """
    def __init__(self):
        """Initialize the speech handler with OpenAI client and audio settings."""
        self.client = OpenAI(api_key=get_conf('OPENAI_API_KEY'))
        
        # Audio settings
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        
        # Initialize audio
        pygame.mixer.init()
        self.p = pyaudio.PyAudio()
        
        LOG.info("Speech handler ready")
    
    def speak(self, text: str):
        """Convert text to speech using OpenAI TTS and play it.
        
        Args:
            text: The text to convert to speech
            
        Returns:
            threading.Thread: The thread handling audio playback
        """
        def _speak():
            try:
                response = self.client.audio.speech.create(
                    model="tts-1",
                    voice="nova",  # Using nova voice which is clear English
                    input=text
                )
                
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    response.stream_to_file(tmp.name)
                    pygame.mixer.music.load(tmp.name)
                    pygame.mixer.music.play()
                    
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                    
                    os.unlink(tmp.name)
                    
            except Exception as e:
                LOG.error(f"TTS Error: {e}")
        
        thread = threading.Thread(target=_speak, daemon=True)
        thread.start()
        return thread
    
    def _record_audio(self, duration: float) -> Optional[bytes]:
        """Record audio from microphone for specified duration.
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Raw audio data as bytes, or None if recording fails
        """
        try:
            stream = self.p.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            frames = []
            for _ in range(int(self.rate / self.chunk * duration)):
                frames.append(stream.read(self.chunk))
            
            stream.stop_stream()
            stream.close()
            return b''.join(frames)
            
        except Exception as e:
            LOG.error(f"Recording error: {e}")
            return None
    
    def _transcribe_audio(self, audio_data: bytes) -> Optional[str]:
        """Transcribe audio data using OpenAI Whisper.
        
        Args:
            audio_data: Raw audio data as bytes
            
        Returns:
            Transcribed text, or None if transcription fails
        """
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                with wave.open(tmp.name, 'wb') as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(self.p.get_sample_size(self.format))
                    wf.setframerate(self.rate)
                    wf.writeframes(audio_data)
                
                with open(tmp.name, "rb") as audio_file:
                    transcript = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="text",
                        language="en"
                    )
                
                os.unlink(tmp.name)
                return transcript.strip() if transcript else None
                
        except Exception as e:
            LOG.error(f"Transcription error: {e}")
            return None
    
    def listen_once(self, timeout: float = 5.0) -> Optional[str]:
        """Record audio and transcribe it to text.
        
        Args:
            timeout: Recording duration in seconds
            
        Returns:
            Transcribed text, or None if no speech detected
        """
        LOG.info("Listening...")
        audio_data = self._record_audio(timeout)
        
        if not audio_data:
            return None
        
        LOG.info("Processing speech...")
        result = self._transcribe_audio(audio_data)
        
        if result:
            LOG.info(f"You said: '{result}'")
            return result
        else:
            LOG.error("No speech detected")
            return None
    
    def get_speech_input(self, prompt: str = "", timeout: float = 10.0) -> Optional[str]:
        """Get speech input with optional text prompt and retry logic.
        
        Args:
            prompt: Optional text prompt to speak before listening
            timeout: Recording timeout in seconds
            
        Returns:
            Transcribed speech text, or None if all attempts fail
        """
        if prompt:
            LOG.info(f"\n{prompt}")
            self.speak(prompt)
            time.sleep(1)
        
        for attempt in range(1, 4):
            if attempt > 1:
                retry_msg = f"Attempt {attempt}/3. Please try again."
                LOG.info(retry_msg)
                self.speak(retry_msg)
                time.sleep(1)
            
            result = self.listen_once(timeout)
            if result:
                return result
            
        LOG.error("Failed to get speech input")
        return None
    
    def test_audio_system(self) -> bool:
        """Test the audio system by speaking and listening.
        
        Returns:
            True if test passes, False otherwise
        """
        LOG.info("Testing audio system...")
        
        try:
            self.speak("Testing speech. Can you hear me?")
            time.sleep(3)
            
            result = self.get_speech_input(
                "Say 'test successful' to verify:", 
                timeout=8.0
            )
            
            if result and "test" in result.lower():
                LOG.info("Audio test passed!")
                return True
            else:
                LOG.error("Audio test failed")
                return False
                
        except Exception as e:
            LOG.error(f"Audio test error: {e}")
            return False
    
    def cleanup(self):
        """Clean up audio resources."""
        try:
            pygame.mixer.quit()
            self.p.terminate()
        except:
            pass