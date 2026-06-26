import torch
import joblib
import numpy as np
from transformers import BertTokenizer, BertForSequenceClassification
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.train_lstm import LSTMModel

load_dotenv()

FEATURE_COLS = [
    "open","high","low","close","volume",
    "ema_20","ema_50","macd","macd_signal","macd_diff",
    "rsi","stoch","bb_high","bb_low","bb_width","atr",
    "obv","returns","log_returns","hl_spread"
]

# Singleton — load sekali, pakai berkali-kali
_lstm_model      = None
_finbert_model   = None
_finbert_tokenizer = None
_ensemble_model  = None
_engine          = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(os.getenv("DATABASE_URL"))
    return _engine

def get_lstm():
    global _lstm_model
    if _lstm_model is None:
        model = LSTMModel(input_size=len(FEATURE_COLS),
                          hidden_size=128, num_layers=2, dropout=0.3)
        model.load_state_dict(torch.load(
            "models/artifacts/lstm_best.pt", map_location="cpu"
        ))
        model.eval()
        _lstm_model = model
    return _lstm_model

def get_finbert():
    global _finbert_model, _finbert_tokenizer
    if _finbert_model is None:
        _finbert_tokenizer = BertTokenizer.from_pretrained("models/artifacts/finbert")
        _finbert_model     = BertForSequenceClassification.from_pretrained("models/artifacts/finbert")
        _finbert_model.eval()
    return _finbert_model, _finbert_tokenizer

def get_ensemble():
    global _ensemble_model
    if _ensemble_model is None:
        _ensemble_model = joblib.load("models/artifacts/ensemble.pkl")
    return _ensemble_model