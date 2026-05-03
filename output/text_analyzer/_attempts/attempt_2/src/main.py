import uvicorn
from fastapi import FastAPI
from src.routes import router

app = FastAPI(title="Text Analyzer Microservice")

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
