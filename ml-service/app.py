from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict

from adapter_crop_predictor import get_predictor


class InputRow(BaseModel):
    crop: str
    temperature: float | None = None
    rainfall: float | None = None
    humidity: float | None = None
    soil_moisture: float | None = None
    nitrogen: float | None = None
    phosphorus: float | None = None
    potassium: float | None = None
    ph: float | None = None


app = FastAPI(title="Krishi AI ML Service")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
def predict(row: InputRow) -> Dict[str, Any]:
    import pandas as pd

    predictor = get_predictor()
    df = pd.DataFrame([row.model_dump()])
    result = predictor.predict_with_confidence(df)
    return {"result": result}


