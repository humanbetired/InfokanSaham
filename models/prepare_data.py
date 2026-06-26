import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.preprocessing import StandardScaler
from dotenv import load_dotenv
import joblib, os

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
os.makedirs("models/artifacts", exist_ok=True)

FEATURE_COLS = [
    "open", "high", "low", "close", "volume",
    "ema_20", "ema_50", "macd", "macd_signal", "macd_diff",
    "rsi", "stoch", "bb_high", "bb_low", "bb_width", "atr",
    "obv", "returns", "log_returns", "hl_spread"
]
TARGET_COL = "target"
SEQUENCE_LEN = 20  

def load_and_prepare():
    print("Loading data...")
    df = pd.read_sql("SELECT * FROM ohlcv_featured ORDER BY ticker, time", engine)
    df["time"] = pd.to_datetime(df["time"])
    df = df.dropna(subset=FEATURE_COLS + [TARGET_COL])

    print(f"Total rows: {len(df)}")

    # Split per ticker supaya tidak ada data leakage antar ticker
    X_train_all, X_test_all = [], []
    y_train_all, y_test_all = [], []

    scaler = StandardScaler()

    for ticker in df["ticker"].unique():
        df_t = df[df["ticker"] == ticker].sort_values("time").reset_index(drop=True)

        features = df_t[FEATURE_COLS].values
        targets  = df_t[TARGET_COL].values

        # 80% train, 20% test — tidak shuffle karena time series
        split = int(len(features) * 0.8)
        X_train_raw = features[:split]
        X_test_raw  = features[split:]
        y_train_raw = targets[:split]
        y_test_raw  = targets[split:]

        # Scale features
        X_train_scaled = scaler.fit_transform(X_train_raw)
        X_test_scaled  = scaler.transform(X_test_raw)

        # Buat sequences (sliding window)
        def make_sequences(X, y, seq_len):
            Xs, ys = [], []
            for i in range(seq_len, len(X)):
                Xs.append(X[i-seq_len:i])
                ys.append(y[i])
            return np.array(Xs), np.array(ys)

        X_tr, y_tr = make_sequences(X_train_scaled, y_train_raw, SEQUENCE_LEN)
        X_te, y_te = make_sequences(X_test_scaled, y_test_raw, SEQUENCE_LEN)

        X_train_all.append(X_tr)
        X_test_all.append(X_te)
        y_train_all.append(y_tr)
        y_test_all.append(y_te)

        print(f"  {ticker}: train={len(X_tr)}, test={len(X_te)}")

    X_train = np.concatenate(X_train_all)
    X_test  = np.concatenate(X_test_all)
    y_train = np.concatenate(y_train_all)
    y_test  = np.concatenate(y_test_all)

    print(f"\nFinal shapes:")
    print(f"  X_train: {X_train.shape}")
    print(f"  X_test:  {X_test.shape}")

    # Simpan ke disk
    np.save("models/artifacts/X_train.npy", X_train)
    np.save("models/artifacts/X_test.npy",  X_test)
    np.save("models/artifacts/y_train.npy", y_train)
    np.save("models/artifacts/y_test.npy",  y_test)
    joblib.dump(scaler, "models/artifacts/scaler.pkl")

    print("\nDone di models/artifacts/")
    return X_train, X_test, y_train, y_test

if __name__ == "__main__":
    load_and_prepare()