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
        # Update status
        supabase_utils.update_agent_status("🚀 Starting real-time search...")
        
        # Start Scraper in a subprocess
        scraper_process = subprocess.Popen(["python3", "scraper.py"], env=os.environ.copy())
        
        print("🤖 BACKGROUND: Parallel Scorer started...")
        # Run Scorer multiple times while scraper is active to give instant feedback
        for i in range(5):
            time.sleep(15) # Wait for some jobs to be saved
            if scraper_process.poll() is not None:
                break # Scraper finished early
            print(f"🤖 BACKGROUND: Mid-scrape scoring run {i+1}")
            subprocess.run(["python3", "score_jobs.py"], env=os.environ.copy())
        
        scraper_process.wait() # Ensure scraper finishes
        
        # Final scoring run
        print("🏁 BACKGROUND: Final scoring run...")
        subprocess.run(["python3", "score_jobs.py"], env=os.environ.copy())
        
        supabase_utils.update_agent_status("🏁 All tasks complete. Happy hunting!")

    background_tasks.add_task(run_automation)

    return {"message": "Searching..."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
