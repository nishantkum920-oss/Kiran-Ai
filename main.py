from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from collections import defaultdict
from datetime import date

# Rate limiter setup (IP-based tracking)
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="NKG AI Studio Global Backend", version="2.0")

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

# Digital Store Daily Downloads tracking (IP -> {date, count})
store_downloads = defaultdict(lambda: {"date": None, "count": 0})

@app.get("/")
def home():
    return {"status": "NKG AI & Digital Store Backend is running live securely!"}

# 1. AI Voice Generation API (Max 5 per day)
@app.post("/api/generate-voice")
@limiter.limit("5/day")
async def generate_voice(request: Request, text: str, lang: str):
    if len(text) > 350:
        raise HTTPException(
            status_code=400, 
            detail="Text is too long! Free tier limit is max 350 characters."
        )
    return {
        "success": True,
        "message": f"Voice generated successfully for language {lang}!",
        "audio_url": "https://example.com/generated-audio.mp3"
    }

# 2. AI Video Generation API (Max 3 per day)
@app.post("/api/generate-video")
@limiter.limit("3/day")
async def generate_video(request: Request, prompt: str, lang: str):
    if len(prompt) > 200:
        raise HTTPException(
            status_code=400, 
            detail="Prompt is too long!"
        )
    return {
        "success": True,
        "message": "Video generation started successfully!",
        "status_url": "https://example.com/video-status"
    }

# 3. Digital Store Download API (Strict Daily 2 Downloads per IP)
@app.post("/api/download-item")
async def download_item(request: Request, item_name: str):
    client_ip = get_remote_address(request)
    today = date.today()
    
    user_data = store_downloads[client_ip]
    
    # Reset count if it's a new day
    if user_data["date"] != today:
        user_data["date"] = today
        user_data["count"] = 0
        
    # Check limit
    if user_data["count"] >= 2:
        raise HTTPException(
            status_code=429,
            detail="⚠️ Daily Free Download Limit Reached! You can download up to 2 items per day."
        )
        
    user_data["count"] += 1
    remaining = 2 - user_data["count"]
    
    return {
        "success": True,
        "item": item_name,
        "message": f"Download started for {item_name}.",
        "remaining_downloads": remaining
    }
