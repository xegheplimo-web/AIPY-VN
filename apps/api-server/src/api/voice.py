from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/voice", tags=["Voice"])


class VoiceSearchRequest(BaseModel):
    audio_base64: str = Field(..., description="Audio file encoded as base64")
    language: str = Field(default="vi", description="Language code: vi, en")
    location: dict = Field(None, description={"lat": float, "lng": float})
    radius_km: float = Field(default=5.0, ge=0.1, le=50.0)


class VoiceSearchResponse(BaseModel):
    transcript: str
    query: str
    summary: str
    stores: list
    total_found: int


@router.post("/search", response_model=VoiceSearchResponse)
async def voice_search(data: VoiceSearchRequest):
    """
    Voice search endpoint.
    
    TODO: In production, integrate with:
    - OpenAI Whisper API for Vietnamese speech-to-text
    - Or local Whisper model (faster-whisper) for privacy
    - Then forward to /api/chat/search with extracted text
    """
    # Mock response for now - in production, decode audio and transcribe
    transcript = "Tim Panadol gan day"
    
    return VoiceSearchResponse(
        transcript=transcript,
        query="Panadol",
        summary="Tim thay 2 cua hang co 'Panadol' gan ban",
        stores=[],
        total_found=0,
    )


@router.post("/upload")
async def voice_upload(
    file: UploadFile = File(...),
    language: str = "vi",
    location_lat: float = None,
    location_lng: float = None,
):
    """
    Upload audio file for voice search.
    Supports .wav, .mp3, .m4a formats.
    
    TODO: Integrate with Whisper API for transcription.
    """
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    # In production: save file, call Whisper, return results
    return {
        "status": "received",
        "filename": file.filename,
        "message": "Audio received. Whisper transcription not yet implemented.",
        "transcript": "Panadol gan day",
    }
