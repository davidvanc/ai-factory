from fastapi import FastAPI
from src.routes import router

app = FastAPI(title="Date Format Converter")

app.include_router(router)
