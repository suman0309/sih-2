from fastapi import FastAPI
from pydantic import BaseModel

from ml_models_precision_adapter import get_engine


class FieldData(BaseModel):
    crop: str = "rice"
    soil_moisture: float = 22.0
    rainfall_mm: float = 0.0
    temperature: float = 30.0
    days_after_sowing: int = 60
    month: int = 7
    nitrogen: float = 30.0
    phosphorus: float = 20.0
    potassium: float = 20.0


app = FastAPI(title="Krishi AI Backend")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/recommend")
def recommend(payload: FieldData):
    engine = get_engine()
    recs, insight = engine.generate_recommendations(payload.model_dump())
    return {"recommendations": recs, "insight": insight}



