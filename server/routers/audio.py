from fastapi import APIRouter, HTTPException, Body, UploadFile, File, WebSocket, WebSocketDisconnect
from server.core.audio import audio_manager
from server.core.i18n import I18N
from fastapi.responses import FileResponse
import uuid
import os
import asyncio
from pathlib import Path

router = APIRouter()

@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Session state
    buffer = bytearray()
    
    try:
        while True:
            # Receive message
            # Format: {"type": "start"|"end"|"data", "data": <bytes/base64>?}
            # Or simpler: Binary frames are audio, Text frames are control.
            
            message = await websocket.receive()
            
            if "bytes" in message:
                # Audio chunk
                buffer.extend(message["bytes"])
                
            elif "text" in message:
                data = message["text"]
                if data == "COMMIT":
                    # Process current buffer
                    if len(buffer) > 0:
                        # Save to temp
                        temp_filename = f"stream_{uuid.uuid4()}.wav"
                        base_dir = Path(__file__).resolve().parents[1]
                        temp_path = str(base_dir / "data" / temp_filename)
                        
                        # Assuming raw PCM 16-bit 16kHz mono, we need to wrap in WAV container
                        # or let audio_manager handle raw. 
                        # Let's save as WAV using scipy or wave
                        import wave
                        with wave.open(temp_path, "wb") as wf:
                            wf.setnchannels(1)
                            wf.setsampwidth(2) # 16-bit
                            wf.setframerate(16000)
                            wf.writeframes(buffer)
                        
                        # Transcribe
                        text = audio_manager.transcribe(temp_path)
                        
                        # Clean up
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                            
                        await websocket.send_json({"type": "transcription", "text": text})
                        buffer = bytearray() # Clear buffer
                        
                elif data == "CLEAR":
                    buffer = bytearray()
                    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WS Error: {e}")

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
        raise HTTPException(status_code=400, detail=I18N.t("invalid_text_length"))

    filename = f"tts_{uuid.uuid4()}.wav"
    base_dir = Path(__file__).resolve().parents[1]
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(data_dir / filename)
    
    success = audio_manager.text_to_speech(text, output_path, speed, volume, voice_id, language)
    
    if not success:
        raise HTTPException(status_code=500, detail=I18N.t("tts_fail"))
        
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
