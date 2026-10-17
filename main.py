import os
import re
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from collections import defaultdict
from datetime import date
import edge_tts

# Audio store directory setup
AUDIO_DIR = "generated_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Kiran-AI Studio Global Backend", version="2.5")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")

store_downloads = defaultdict(lambda: {"date": None, "count": 0})

@app.get("/")
def home():
    return {"status": "Kiran-AI Studio Backend is active!"}

VOICE_MAPPING = {
    "Hindi": "hi-IN-SwaraNeural",
    "English": "en-US-ChristopherNeural",
    "Bhojpuri": "hi-IN-MadhurNeural",
    "Spanish": "es-ES-AlvaroNeural",
    "French": "fr-FR-DeniseNeural",
    "German": "de-DE-ConradNeural",
    "Japanese": "ja-JP-NanamiNeural",
    "Chinese": "zh-CN-XiaoxiaoNeural",
    "Arabic": "ar-SA-HamedNeural",
    "Bengali": "bn-IN-TanishaaNeural"
}

@app.post("/api/generate-voice")
@limiter.limit("20/day")
async def generate_voice(request: Request, text: str, lang: str):
    if len(text) > 5000:
        raise HTTPException(
            status_code=400, 
            detail="Text is too long! Max limit is 5000 characters."
        )
    
    # Clean text to prevent TTS truncation
    clean_text = re.sub(r'[\r\n"]+', ' ', text).strip()
    if not clean_text:
        raise HTTPException(status_code=400, detail="Provided text is empty.")

    voice = VOICE_MAPPING.get(lang, "hi-IN-SwaraNeural")
    filename = f"voice_{abs(hash(clean_text + lang))}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)

    try:
        communicate = edge_tts.Communicate(clean_text, voice)
        await communicate.save(filepath)

        base_url = str(request.base_url).rstrip("/")
        audio_url = f"{base_url}/audio/{filename}"

        return {
            "success": True,
            "message": f"Full Voiceover generated for {lang}!",
            "audio_url": audio_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice generation error: {str(e)}")

@app.post("/api/generate-video")
@limiter.limit("10/day")
async def generate_video(request: Request, prompt: str, lang: str, script: str = ""):
    full_text = script if script.strip() else prompt
    if len(full_text) > 5000:
        raise HTTPException(status_code=400, detail="Prompt/Script too long!")

    clean_script = re.sub(r'[\r\n"]+', ' ', full_text).strip()
    voice = VOICE_MAPPING.get(lang, "hi-IN-SwaraNeural")
    
    filename = f"vid_voice_{abs(hash(clean_script + lang))}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)

    try:
        # 1. Generate full speech MP3
        communicate = edge_tts.Communicate(clean_script, voice)
        await communicate.save(filepath)

        base_url = str(request.base_url).rstrip("/")
        audio_url = f"{base_url}/audio/{filename}"

        # 2. Generate Cinematic 3D Scene Visual (Free High Quality Render)
        clean_prompt = prompt.replace(" ", "%20")
        media_url = f"https://image.pollinations.ai/prompt/3D%20cinematic%20photorealistic%20documentary%20scene,%20{clean_prompt}?width=1280&height=720&nologo=true"

        return {
            "success": True,
            "message": "AI Documentary Scene & Full Voiceover Created!",
            "status_url": media_url,
            "audio_url": audio_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
