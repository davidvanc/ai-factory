from fastapi import FastAPI, Query, HTTPException
from src.converter import convert_number_to_dutch_text

app = FastAPI()


@app.get("/convert")
async def convert(number: str = Query(..., description="Getal om te zetten naar Nederlandse tekst")):
    try:
        result = convert_number_to_dutch_text(number)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"text": result}
