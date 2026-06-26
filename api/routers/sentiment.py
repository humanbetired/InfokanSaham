from fastapi import APIRouter
from pydantic import BaseModel
import torch
from api.dependencies import get_finbert

router = APIRouter(prefix="/sentiment", tags=["Sentiment"])

class SentimentRequest(BaseModel):
    text: str

class SentimentResponse(BaseModel):
    text: str
    label: str
    score: float
    positive_proba: float
    neutral_proba: float
    negative_proba: float

@router.post("/", response_model=SentimentResponse)
def analyze_sentiment(req: SentimentRequest):
    model, tokenizer = get_finbert()

    enc = tokenizer(req.text[:512], max_length=128,
                    truncation=True, padding="max_length",
                    return_tensors="pt")

    with torch.no_grad():
        logits = model(**enc).logits
        proba  = torch.softmax(logits, dim=1).squeeze().numpy()

    labels    = ["positive", "neutral", "negative"]
    label_idx = proba.argmax()

    return SentimentResponse(
        text=req.text,
        label=labels[label_idx],
        score=round(float(proba[0] - proba[2]), 4),
        positive_proba=round(float(proba[0]), 4),
        neutral_proba=round(float(proba[1]), 4),
        negative_proba=round(float(proba[2]), 4),
    )