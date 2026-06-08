"""
Voice Search Service using faster-whisper

Provides speech-to-text functionality for Vietnamese voice search.
"""

import logging
import os
import tempfile

try:
    from faster_whisper import WhisperModel

    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

logger = logging.getLogger(__name__)

# Mapping of common audio MIME types to file extensions
AUDIO_MIME_TO_EXT = {
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/ogg": ".ogg",
    "audio/x-ogg": ".ogg",
    "audio/webm": ".webm",
    "audio/x-webm": ".webm",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
    "audio/flac": ".flac",
    "audio/x-flac": ".flac",
}

# Set of supported audio extensions
SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".ogg", ".webm", ".m4a", ".flac"}


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
        if not WHISPER_AVAILABLE:
            logger.warning("faster-whisper not installed, voice search disabled")
            return

        try:
            logger.info(f"Loading Whisper model: {self.model_size}")
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type="int8",  # Use int8 for faster inference
            )
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            self.model = None

    def _get_extension_for_bytes(
        self, audio_bytes: bytes, content_type: str | None = None
    ) -> str:
        """
        Determine the file extension for audio bytes.

        Uses the content_type hint if available, otherwise falls back to
        magic-byte detection for common formats.

        Args:
            audio_bytes: Raw audio data
            content_type: Optional MIME type hint

        Returns:
            File extension string (e.g., '.webm')
        """
        # Try MIME type first
        if content_type and content_type in AUDIO_MIME_TO_EXT:
            return AUDIO_MIME_TO_EXT[content_type]

        # Magic byte detection
        if audio_bytes[:4] == b"RIFF" and audio_bytes[8:12] == b"WAVE":
            return ".wav"
        if audio_bytes[:3] == b"ID3" or audio_bytes[:2] == b"\xff\xfb":
            return ".mp3"
        if audio_bytes[:4] == b"OggS":
            return ".ogg"
        if audio_bytes[:4] == b"\x1a\x45\xdf\xa5":
            return ".webm"  # EBML header = Matroska/WebM
        if audio_bytes[:4] == b"fLaC":
            return ".flac"

        # Default to webm (most common for browser MediaRecorder)
        return ".webm"

    async def transcribe_audio(
        self, audio_path: str, language: str | None = None
    ) -> str:
        """
        Transcribe audio file to text.

        Args:
            audio_path: Path to audio file
            language: Language code (default: Vietnamese)

        Returns:
            Transcribed text

        Raises:
            RuntimeError: If the Whisper model is not loaded
            FileNotFoundError: If the audio file does not exist
        """
        if not self.model:
            raise RuntimeError(
                "Whisper model is not loaded. Voice search service is unavailable."
            )

        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        try:
            segments, info = self.model.transcribe(
                audio_path,
                language=language or self.language,
                beam_size=5,
                vad_filter=True,
                vad_parameters={
                    "min_speech_duration_ms": 250,
                    "speech_pad_ms": 30,
                },
            )

            # Combine all segments
            text = " ".join([segment.text.strip() for segment in segments]).strip()

            logger.info(
                f"Transcription completed: {len(text)} characters, "
                f"language={info.language}, probability={info.language_probability:.2f}"
            )
            return text

        except Exception as e:
            logger.error(f"Transcription error for {audio_path}: {e}")
            raise RuntimeError(f"Transcription failed: {e}") from e

    async def transcribe_audio_bytes(
        self,
        audio_bytes: bytes,
        language: str | None = None,
        content_type: str | None = None,
    ) -> str:
        """
        Transcribe audio bytes to text.

        Writes the audio bytes to a temporary file, runs Whisper
        transcription, and cleans up the temp file afterwards.

        Args:
            audio_bytes: Audio data as raw bytes
            language: Language code (default: Vietnamese)
            content_type: Optional MIME type to help determine audio format

        Returns:
            Transcribed text

        Raises:
            RuntimeError: If the Whisper model is not loaded
            ValueError: If audio_bytes is empty
        """
        if not self.model:
            raise RuntimeError(
                "Whisper model is not loaded. Voice search service is unavailable."
            )

        if not audio_bytes:
            raise ValueError("Audio bytes cannot be empty")

        # Determine the file extension
        extension = self._get_extension_for_bytes(audio_bytes, content_type)

        temp_path = None
        try:
            # Write audio bytes to a temporary file
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=extension, prefix="voice_"
            ) as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name

            logger.info(
                f"Wrote {len(audio_bytes)} bytes to temp file: {temp_path} "
                f"(content_type={content_type}, ext={extension})"
            )

            # Transcribe using the file-based method
            text = await self.transcribe_audio(temp_path, language=language)

            if not text:
                logger.warning("Transcription returned empty text")
                return ""

            return text

        except (RuntimeError, FileNotFoundError, ValueError):
            # Re-raise known exceptions as-is
            raise
        except Exception as e:
            logger.error(f"Transcription from bytes failed: {e}")
            raise RuntimeError(f"Transcription from bytes failed: {e}") from e
        finally:
            # Always clean up the temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                    logger.debug(f"Cleaned up temp file: {temp_path}")
                except OSError as cleanup_err:
                    logger.warning(
                        f"Failed to clean up temp file {temp_path}: {cleanup_err}"
                    )

    def is_ready(self) -> bool:
        """Check if the service is ready (model loaded)."""
        return self.model is not None


# Global service instance
voice_service = VoiceSearchService()


def get_voice_service() -> VoiceSearchService:
    """Get the global voice service instance."""
    return voice_service
