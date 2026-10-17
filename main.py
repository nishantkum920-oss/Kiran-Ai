import os
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

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Kiran-AI Studio Global Backend", version="2.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Enable CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated audio files publicly
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")

# Digital Store Daily Downloads tracking
store_downloads = defaultdict(lambda: {"date": None, "count": 0})

@app.get("/")
def home():
    return {"status": "Kiran-AI Studio Backend is live with Free Real Audio Synthesis!"}

# Language mapping for Free Microsoft Edge-TTS
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

# 1. Real AI Voice Generation API (100% Free)
@app.post("/api/generate-voice")
@limiter.limit("10/day")
async def generate_voice(request: Request, text: str, lang: str):
    if len(text) > 5000:
        raise HTTPException(
            status_code=400, 
            detail="Text is too long! Max limit is 5000 characters."
        )
    
    voice = VOICE_MAPPING.get(lang, "hi-IN-SwaraNeural")
    filename = f"voice_{hash(text + lang) & 0xffffffff}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)

    try:
        # Generate real speech using free Edge-TTS
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(filepath)

        # Base URL for playing audio
        base_url = str(request.base_url).rstrip("/")
        audio_url = f"{base_url}/audio/{filename}"

        return {
            "success": True,
            "message": f"Real Voice generated successfully for {lang}!",
            "audio_url": audio_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice generation failed: {str(e)}")

# 2. AI Video Generation API (Free Pollinations Media Integration)
@app.post("/api/generate-video")
@limiter.limit("5/day")
async def generate_video(request: Request, prompt: str, lang: str):
    if len(prompt) > 5000:
        raise HTTPException(
            status_code=400, 
            detail="Prompt is too long! Max limit is 5000 characters."
        )
    
    # Generate direct free AI media stream using Pollinations API
    clean_prompt = prompt.replace(" ", "%20")
    media_url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1280&height=720&nologo=true"

    return {
        "success": True,
        "message": "AI Scene Visual generated successfully!",
        "status_url": media_url
    }

# 3. Digital Store Download API
@app.post("/api/download-item")
async def download_item(request: Request, item_name: str):
    client_ip = get_remote_address(request)
    today = date.today()
    
    user_data = store_downloads[client_ip]
    
    if user_data["date"] != today:
        user_data["date"] = today
        user_data["count"] = 0
        
    if user_data["count"] >= 5:
        raise HTTPException(
            status_code=429,
            detail="⚠️ Daily Limit Reached! You can download up to 5 items per day."
        )
        
    user_data["count"] += 1
    remaining = 5 - user_data["count"]
    
    return {
        "success": True,
        "item": item_name,
        "message": f"Download started for {item_name}.",
        "remaining_downloads": remaining
    }
