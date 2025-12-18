from fastapi import APIRouter, HTTPException, Body, UploadFile, File
from server.core.audio import audio_manager
from fastapi.responses import FileResponse
import uuid
import os
from pathlib import Path

router = APIRouter()

@router.get("/voices")
async def get_available_voices():
    return audio_manager.get_voices()

@router.post("/tts")
async def text_to_speech_endpoint(
    text: str = Body(..., embed=True),
    speed: float = Body(1.0, embed=True),
    volume: float = Body(1.0, embed=True),
    voice_id: str = Body("default", embed=True),
    language: str = Body("zh", embed=True)
):
    if not text or len(text) > 500:
        raise HTTPException(status_code=400, detail="Invalid text length (1-500 chars)")

    filename = f"tts_{uuid.uuid4()}.wav"
    base_dir = Path(__file__).resolve().parents[1]
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(data_dir / filename)
    
    success = audio_manager.text_to_speech(text, output_path, speed, volume, voice_id, language)
    
    if not success:
        raise HTTPException(status_code=500, detail="TTS generation failed or disabled")
        
    return FileResponse(output_path, media_type="audio/wav", filename=filename)

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    base_dir = Path(__file__).resolve().parents[1]
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    temp_path = str(data_dir / f"temp_{file.filename}")
    with open(temp_path, "wb") as f:
        f.write(await file.read())
    
    text = audio_manager.transcribe(temp_path)
    
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    return {"text": text}
