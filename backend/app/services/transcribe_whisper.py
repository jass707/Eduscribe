"""
Lazy-loading faster-whisper wrapper for EduScribe backend.
Based on your existing transcribe_whisper.py
"""
import os
import threading
from typing import Dict, Any
from app.core.config import settings

# Dev helper for Windows OMP issue (dev-only)
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")

# Module-level placeholders
_model = None
_model_lock = threading.Lock()

def _load_model():
    """Load the Whisper model once, thread-safe."""
    global _model
    if _model is not None:
        return _model

    with _model_lock:
        if _model is None:
            # import inside function to avoid import-time dependency issues
            from faster_whisper import WhisperModel
            print(f"[whisper] Loading model: {settings.WHISPER_MODEL_SIZE} device={settings.WHISPER_DEVICE} compute={settings.WHISPER_COMPUTE_TYPE}")
            _model = WhisperModel(
                settings.WHISPER_MODEL_SIZE, 
                device=settings.WHISPER_DEVICE, 
                compute_type=settings.WHISPER_COMPUTE_TYPE
            )
            print("[whisper] Model loaded.")
    return _model

def transcribe_local(audio_path: str, beam_size: int = 5) -> Dict[str, Any]:
    """
    Transcribe an audio file using the (lazy-loaded) faster-whisper model.
    Returns a dict with 'text', 'segments', 'language', 'duration', etc.
    """
    model = _load_model()
    segments, info = model.transcribe(audio_path, beam_size=beam_size)

    transcript_text = ""
    results = []
    for segment in segments:
        results.append({
            "start": float(segment.start),
            "end": float(segment.end),
            "text": segment.text.strip()
        })
        transcript_text += segment.text.strip() + " "

    return {
        "text": transcript_text.strip(),
        "segments": results,
        "language": getattr(info, "language", "unknown"),
        "language_probability": getattr(info, "language_probability", None),
        "duration": getattr(info, "duration", None),
        "info": repr(info),
    }

async def transcribe_audio_chunk(audio_path: str) -> Dict[str, Any]:
    """
    Async wrapper for transcription to be used in FastAPI endpoints.
    """
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, transcribe_local, audio_path)
