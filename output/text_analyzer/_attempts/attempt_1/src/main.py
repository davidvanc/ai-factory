from fastapi import FastAPI
from src.routes import router

app = FastAPI(title="Text Analyzer Microservice")

app.include_router(router)
