"""
Voice Search Service using faster-whisper

Provides speech-to-text functionality for Vietnamese voice search.
"""

import logging
from typing import Optional
from faster_whisper import WhisperModel
from src.config import config
import os

logger = logging.getLogger(__name__)


class VoiceSearchService:
    """Service for speech-to-text using faster-whisper."""
    
    def __init__(self):
        """Initialize voice search service."""
        self.model = None
        self.model_size = "base"  # base, small, medium, large
        self.language = "vi"  # Vietnamese
        self.device = "cpu"  # cpu or cuda
        self._load_model()
    
    def _load_model(self):
        """Load the Whisper model."""
        try:
            # Try to load the model
            logger.info(f"Loading Whisper model: {self.model_size}")
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type="int8"  # Use int8 for faster inference
            )
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            self.model = None
    
    async def transcribe_audio(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> str:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file
            language: Language code (default: Vietnamese)
        
        Returns:
            Transcribed text
        """
        if not self.model:
            logger.warning("Whisper model not loaded, returning mock response")
            return "Xin lỗi, dịch vụ giọng nói chưa sẵn sàng."
        
        try:
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            # Transcribe audio
            segments, info = self.model.transcribe(
                audio_path,
                language=language or self.language,
                beam_size=5,
                vad_filter=True,
                vad_parameters={
                    "min_speech_duration_ms": 250,
                    "speech_pad_ms": 30,
                }
            )
            
            # Combine all segments
            text = " ".join([segment.text for segment in segments])
            
            logger.info(f"Transcription completed: {len(text)} characters")
            return text
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return "Xin lỗi, không thể chuyển đổi giọng nói thành văn bản."
    
    async def transcribe_audio_bytes(
        self,
        audio_bytes: bytes,
        language: Optional[str] = None
    ) -> str:
        """
        Transcribe audio bytes to text.
        
        Args:
            audio_bytes: Audio data as bytes
            language: Language code (default: Vietnamese)
        
        Returns:
            Transcribed text
        """
        if not self.model:
            logger.warning("Whisper model not loaded, returning mock response")
            return "Xin lỗi, dịch vụ giọng nói chưa sẵn sàng."
        
        try:
            # For now, this is a placeholder
            # In production, we would save bytes to temp file and transcribe
            logger.warning("Transcription from bytes not implemented yet")
            return "Xin lỗi, tính năng này đang được phát triển."
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return "Xin lỗi, không thể chuyển đổi giọng nói thành văn bản."
    
    def is_ready(self) -> bool:
        """Check if the service is ready."""
        return self.model is not None


# Global service instance
voice_service = VoiceSearchService()


def get_voice_service() -> VoiceSearchService:
    """Get the global voice service instance."""
    return voice_service
