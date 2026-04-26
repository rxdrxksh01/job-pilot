from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import os
import config
from supabase_utils import supabase

app = FastAPI()

# Allow frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    query: str
    location: str = "India"
    user_id: str

@app.post("/scrape")
async def trigger_scrape(request: SearchRequest, background_tasks: BackgroundTasks):
    # 1. Clear ALL old jobs for this user immediately (Normal Search Engine behavior)
    try:
        supabase.table("jobs").delete().eq("user_id", request.user_id).execute()
        
        # 2. Update preferences for the scraper
        supabase.table("user_preferences").upsert({
            "user_id": request.user_id,
            "linkedin_search_queries": [request.query],
            "location": request.location
        }, on_conflict="user_id").execute()
    except Exception as e:
        print(f"Error preparing database: {e}")

    # 3. Run scraper and then scoring in background
    def run_automation():
        print(f"🚀 PHASE 1: Starting Scraper for '{request.query}'")
        subprocess.run(["python3", "scraper.py"], env=os.environ.copy())
        
        print("✅ PHASE 1 COMPLETE: Scraping finished.")
        print("🤖 PHASE 2: Starting AI Match Scoring...")
        
        # Run AI Scorer
        subprocess.run(["python3", "score_jobs.py"], env=os.environ.copy())
        print("🏁 ALL PHASES COMPLETE: AI Scoring finished.")

    background_tasks.add_task(run_automation)

    return {"message": "Searching..."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
