from app.models import Prediction, SessionLocal
from fastapi import FastAPI, Header, HTTPException, Depends, Request
from pydantic import BaseModel
import numpy as np
import os
from app.classifier import classify_batch
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != os.getenv("SECRET_API_KEY"):
        raise HTTPException(
            status_code=401, detail="Invalid API key")

limiter = Limiter(key_func=get_remote_address)

class ClassifyRequest(BaseModel):
    pixels: list[list[int]]

class ClassifyResponse(BaseModel):
    prediction: str
    confidence: float
    scores: dict[str, float]
    id: int
class FeedbackRequest(BaseModel):
    label: str

app = FastAPI()
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
@app.get("/health")
def health():
    return {"status": "ok", "model_version": "v1"}

@app.get("/results")
def results():
    db = SessionLocal()
    rows = (db.query(Prediction)
        .order_by(Prediction.created_at.desc())
        .limit(20).all())
    db.close()
    return {"results": [
        {"id": r.id,
         "prediction": r.prediction,
         "confidence": r.confidence,
         "model_version": r.model_version,
         "created_at": r.created_at.isoformat()}
        for r in rows]}

@app.post("/classify",
          response_model=ClassifyResponse,
          dependencies=[Depends(verify_api_key)])
@limiter.limit("30/minute")
def classify(request: Request, req: ClassifyRequest):
    arr = np.array(req.pixels, dtype=np.uint8)[np.newaxis]
    result = classify_batch(arr)[0]
    db = SessionLocal()
    pred = Prediction(
        prediction=result["prediction"],
        confidence=result["confidence"],
        model_version="v1")
    db.add(pred)
    db.commit()
    db.refresh(pred)
    pred_id = pred.id
    db.close()
    return {**result, "id": pred_id}

@app.patch("/feedback/{prediction_id}")
def feedback(prediction_id: int, req: FeedbackRequest):
    db = SessionLocal()
    pred = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not pred:
        db.close()
        raise  HTTPException(status_code=404, detail="Prediction not found")
    pred.label = req.label
    db.commit()
    db.close()
    return {"id": prediction_id, "label": req.label}
