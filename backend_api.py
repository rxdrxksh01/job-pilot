from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import os
import sys
import traceback
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

@app.get("/health")
async def health():
    """Health check endpoint to verify the server is running."""
    return {"status": "ok", "python": sys.version}

@app.post("/scrape")
async def trigger_scrape(request: SearchRequest, background_tasks: BackgroundTasks):
    print(f"🟢 /scrape called: query='{request.query}', location='{request.location}', user='{request.user_id}'")
    
    # 1. Clear ALL old jobs for this user immediately
    try:
        del_result = supabase.table("jobs").delete().eq("user_id", request.user_id).execute()
        print(f"🗑️ Deleted old jobs: {del_result}")
        
        # 2. Update preferences for the scraper
        pref_result = supabase.table("user_preferences").upsert({
            "user_id": request.user_id,
            "linkedin_search_queries": [request.query],
            "location": request.location
        }, on_conflict="user_id").execute()
        print(f"📝 Updated preferences: {pref_result}")
    except Exception as e:
        print(f"❌ Error preparing database: {e}")
        traceback.print_exc()

    # 3. Set CLERK_USER_ID so scraper knows which user to save for
    env = os.environ.copy()
    env["CLERK_USER_ID"] = request.user_id
    print(f"🔑 Setting CLERK_USER_ID={request.user_id}")

    # 4. Run scraper in background
    def run_automation():
        try:
            print("🤖 BACKGROUND: Scraper starting...")
            result = subprocess.run(
                ["python3", "scraper.py"], 
                env=env, 
                capture_output=True, 
                text=True,
                timeout=300  # 5 minute timeout
            )
            print(f"🏁 BACKGROUND: Scraper finished. Return code: {result.returncode}")
            if result.stdout:
                print(f"📄 STDOUT (last 2000 chars):\n{result.stdout[-2000:]}")
            if result.stderr:
                print(f"⚠️ STDERR (last 2000 chars):\n{result.stderr[-2000:]}")
        except subprocess.TimeoutExpired:
            print("⏰ BACKGROUND: Scraper timed out after 5 minutes!")
        except Exception as e:
            print(f"💥 BACKGROUND: Scraper crashed: {e}")
            traceback.print_exc()

    background_tasks.add_task(run_automation)

    return {"message": "Searching...", "user_id": request.user_id, "query": request.query}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
