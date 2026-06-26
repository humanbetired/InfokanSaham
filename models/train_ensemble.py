import numpy as np
import pandas as pd
import torch
import joblib
import mlflow
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from transformers import BertTokenizer, BertForSequenceClassification
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os, sys

load_dotenv()
mlflow.set_tracking_uri("sqlite:///mlops/mlflow.db")
mlflow.set_experiment("InfokanSaham")

engine = create_engine(os.getenv("DATABASE_URL"))

sys.path.append("models")
from train_lstm import LSTMModel

FEATURE_COLS = [
    "open","high","low","close","volume",
    "ema_20","ema_50","macd","macd_signal","macd_diff",
    "rsi","stoch","bb_high","bb_low","bb_width","atr",
    "obv","returns","log_returns","hl_spread"
]

def get_lstm_proba(X_test):
    model = LSTMModel(input_size=len(FEATURE_COLS),
                      hidden_size=128, num_layers=2, dropout=0.3)
    model.load_state_dict(torch.load("models/artifacts/lstm_best.pt"))
    model.eval()
    with torch.no_grad():
        proba = model(torch.FloatTensor(X_test)).squeeze().numpy()
    return proba

def get_finbert_proba(texts):
    tokenizer = BertTokenizer.from_pretrained("models/artifacts/finbert")
    model     = BertForSequenceClassification.from_pretrained("models/artifacts/finbert")
    model.eval()

    scores = []
    for text in texts:
        enc = tokenizer(str(text), max_length=128, truncation=True,
                        padding="max_length", return_tensors="pt")
        with torch.no_grad():
            logits = model(**enc).logits
            proba  = torch.softmax(logits, dim=1).squeeze().numpy()
            # positive prob - negative prob → sentiment score
            sentiment = float(proba[0] - proba[2])
        scores.append(sentiment)
    return np.array(scores)

def train():
    X_test  = np.load("models/artifacts/X_test.npy")
    y_test  = np.load("models/artifacts/y_test.npy")

    # Load news untuk dapat sentiment
    df_news = pd.read_sql("SELECT text, sentiment_score FROM news_sentiment", engine)
    texts   = df_news["text"].tolist()[:len(X_test)]

    # Pad kalau news lebih sedikit dari X_test
    while len(texts) < len(X_test):
        texts.append("market neutral")

    print("Getting LSTM probabilities...")
    lstm_proba = get_lstm_proba(X_test)

    print("Getting FinBERT probabilities...")
    finbert_proba = get_finbert_proba(texts[:len(X_test)])

    # Stack features untuk ensemble
    ensemble_features = np.column_stack([lstm_proba, finbert_proba])

    # Split 50/50 untuk train ensemble
    split    = len(ensemble_features) // 2
    X_ens_tr = ensemble_features[:split]
    X_ens_te = ensemble_features[split:]
    y_ens_tr = y_test[:split]
    y_ens_te = y_test[split:]

    with mlflow.start_run(run_name="Ensemble_v1"):
        ensemble_model = LogisticRegression()
        ensemble_model.fit(X_ens_tr, y_ens_tr)

        preds   = ensemble_model.predict(X_ens_te)
        acc     = accuracy_score(y_ens_te, preds)

        mlflow.log_metric("ensemble_accuracy", acc)
        joblib.dump(ensemble_model, "models/artifacts/ensemble.pkl")

        print("\n=== Ensemble Classification Report ===")
        print(classification_report(y_ens_te, preds,
              target_names=["Turun", "Naik"]))

        print(f"\nEnsemble selesai — accuracy: {acc:.4f}")

if __name__ == "__main__":
    train()