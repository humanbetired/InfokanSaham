from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
import torch
from sklearn.preprocessing import StandardScaler
from api.dependencies import get_engine, get_lstm, get_ensemble, get_finbert, FEATURE_COLS

router = APIRouter(prefix="/predict", tags=["Prediction"])

SEQUENCE_LEN = 20

class PredictRequest(BaseModel):
    ticker: str
    news_text: str = "market neutral"

class PredictResponse(BaseModel):
    ticker: str
    prediction: str
    confidence: float
    lstm_proba: float
    sentiment_score: float
    recommendation: str

@router.post("/", response_model=PredictResponse)
def predict(req: PredictRequest):
    engine = get_engine()

    # Load data ticker
    df = pd.read_sql(f"""
        SELECT * FROM ohlcv_featured
        WHERE ticker = '{req.ticker}'
        ORDER BY time DESC
        LIMIT {SEQUENCE_LEN + 5}
    """, engine)

    if len(df) < SEQUENCE_LEN:
        raise HTTPException(status_code=404,
            detail=f"Data tidak cukup untuk ticker {req.ticker}")

    df = df.sort_values("time").reset_index(drop=True)
    df = df.dropna(subset=FEATURE_COLS)

    # Scale & predict LSTM
    features = df[FEATURE_COLS].values
    scaler   = StandardScaler()
    scaled   = scaler.fit_transform(features)
    seq      = torch.FloatTensor(scaled[-SEQUENCE_LEN:]).unsqueeze(0)

    lstm_model = get_lstm()
    with torch.no_grad():
        logit      = lstm_model(seq)
        lstm_proba = torch.sigmoid(logit).item()

    # Sentiment FinBERT
    finbert_model, tokenizer = get_finbert()
    enc = tokenizer(req.news_text[:512], max_length=128,
                    truncation=True, padding="max_length",
                    return_tensors="pt")
    with torch.no_grad():
        logits   = finbert_model(**enc).logits
        proba    = torch.softmax(logits, dim=1).squeeze().numpy()
        sentiment_score = float(proba[0] - proba[2])  # positive - negative

    # Ensemble
    ensemble      = get_ensemble()
    features_ens  = np.array([[lstm_proba, sentiment_score]])
    final_pred    = ensemble.predict(features_ens)[0]
    final_proba   = ensemble.predict_proba(features_ens)[0].max()

    prediction    = "NAIK" if final_pred == 1 else "TURUN"
    recommendation = (
        "BUY 🟢"  if prediction == "NAIK" and final_proba > 0.65 else
        "SELL 🔴" if prediction == "TURUN" and final_proba > 0.65 else
        "HOLD 🟡"
    )

    return PredictResponse(
        ticker=req.ticker,
        prediction=prediction,
        confidence=round(final_proba, 4),
        lstm_proba=round(lstm_proba, 4),
        sentiment_score=round(sentiment_score, 4),
        recommendation=recommendation,
    )