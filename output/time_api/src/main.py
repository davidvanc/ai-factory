from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from src.time_service import get_current_time

app = FastAPI(title="Time API", description="A simple REST API that returns the current time in JSON format")

@app.get("/")
async def root():
    return {"message": "Welcome to Time API! Use /time to get the current time."}

@app.get("/time")
async def get_time():
    current_time = get_current_time()
    return JSONResponse(content={"current_time": current_time.isoformat()})
