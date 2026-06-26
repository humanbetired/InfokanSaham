import numpy as np
import pandas as pd
import torch
import joblib
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sklearn.preprocessing import StandardScaler
import mlflow
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
SEQUENCE_LEN = 20
INITIAL_CAPITAL = 10_000_000  # 10 juta rupiah

# ── Load Models ──────────────────────────────────────────
def load_lstm():
    model = LSTMModel(input_size=len(FEATURE_COLS),
                      hidden_size=128, num_layers=2, dropout=0.3)
    model.load_state_dict(torch.load("models/artifacts/lstm_best.pt",
                                     map_location="cpu"))
    model.eval()
    return model

# ── Generate Predictions ─────────────────────────────────
def generate_predictions(df_ticker):
    model  = load_lstm()
    scaler = StandardScaler()

    features = df_ticker[FEATURE_COLS].values
    scaler.fit(features)
    scaled = scaler.transform(features)

    preds, probas = [], []
    for i in range(SEQUENCE_LEN, len(scaled)):
        seq = torch.FloatTensor(scaled[i-SEQUENCE_LEN:i]).unsqueeze(0)
        with torch.no_grad():
            logit = model(seq)
            proba = torch.sigmoid(logit).item()
            pred  = 1 if proba > 0.5 else 0
        preds.append(pred)
        probas.append(proba)

    return preds, probas

# ── Backtesting Strategy ─────────────────────────────────
def backtest_ticker(ticker):
    print(f"\n{'='*50}")
    print(f"Backtesting: {ticker}")
    print(f"{'='*50}")

    df = pd.read_sql(f"""
        SELECT * FROM ohlcv_featured
        WHERE ticker = '{ticker}'
        ORDER BY time
    """, engine)
    df["time"] = pd.to_datetime(df["time"])
    df = df.dropna(subset=FEATURE_COLS).reset_index(drop=True)

    # Generate predictions
    preds, probas = generate_predictions(df)

    # Align dengan data (potong SEQUENCE_LEN baris awal)
    df_bt = df.iloc[SEQUENCE_LEN:].copy().reset_index(drop=True)
    df_bt["pred"]  = preds
    df_bt["proba"] = probas

    # ── Strategy 1: Model Strategy ───────────────────────
    # Beli kalau model prediksi Naik, jual kalau prediksi Turun
    capital      = INITIAL_CAPITAL
    position     = 0  # jumlah saham yang dipegang
    capital_hist = []
    trades       = []

    for i, row in df_bt.iterrows():
        price = row["close"]

        if row["pred"] == 1 and position == 0:
            # BUY
            position  = capital / price
            capital   = 0
            trades.append({"date": row["time"], "action": "BUY", "price": price})

        elif row["pred"] == 0 and position > 0:
            # SELL
            capital  = position * price
            position = 0
            trades.append({"date": row["time"], "action": "SELL", "price": price})

        # Portfolio value
        portfolio_value = capital + (position * price)
        capital_hist.append(portfolio_value)

    # Tutup posisi di akhir
    if position > 0:
        capital = position * df_bt.iloc[-1]["close"]

    df_bt["model_portfolio"] = capital_hist

    # ── Strategy 2: Buy and Hold ─────────────────────────
    first_price = df_bt.iloc[0]["close"]
    shares_held = INITIAL_CAPITAL / first_price
    df_bt["buyhold_portfolio"] = shares_held * df_bt["close"]

    # ── Metrics ──────────────────────────────────────────
    model_return   = (df_bt["model_portfolio"].iloc[-1] - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
    buyhold_return = (df_bt["buyhold_portfolio"].iloc[-1] - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100

    # Sharpe Ratio (simplified)
    daily_returns  = df_bt["model_portfolio"].pct_change().dropna()
    sharpe         = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)

    # Max Drawdown
    rolling_max    = df_bt["model_portfolio"].cummax()
    drawdown       = (df_bt["model_portfolio"] - rolling_max) / rolling_max
    max_drawdown   = drawdown.min() * 100

    # Win Rate
    df_trades = pd.DataFrame(trades)
    win_rate  = 0
    if len(df_trades) >= 2:
        buy_prices  = df_trades[df_trades["action"] == "BUY"]["price"].values
        sell_prices = df_trades[df_trades["action"] == "SELL"]["price"].values
        min_len     = min(len(buy_prices), len(sell_prices))
        if min_len > 0:
            wins     = (sell_prices[:min_len] > buy_prices[:min_len]).sum()
            win_rate = wins / min_len * 100

    print(f"Initial Capital  : Rp {INITIAL_CAPITAL:,.0f}")
    print(f"Model Return     : {model_return:+.2f}%")
    print(f"Buy & Hold Return: {buyhold_return:+.2f}%")
    print(f"Sharpe Ratio     : {sharpe:.2f}")
    print(f"Max Drawdown     : {max_drawdown:.2f}%")
    print(f"Win Rate         : {win_rate:.1f}%")
    print(f"Total Trades     : {len(df_trades)}")

    return df_bt, {
        "ticker":          ticker,
        "model_return":    round(model_return, 2),
        "buyhold_return":  round(buyhold_return, 2),
        "sharpe":          round(sharpe, 2),
        "max_drawdown":    round(max_drawdown, 2),
        "win_rate":        round(win_rate, 2),
        "total_trades":    len(df_trades),
    }

# ── Visualization ─────────────────────────────────────────
def plot_backtest(df_bt, ticker):
    fig = make_subplots(rows=3, cols=1,
        shared_xaxes=True,
        subplot_titles=[
            f"{ticker} — Portfolio Value: Model vs Buy & Hold",
            "Prediksi Model (1=Naik, 0=Turun)",
            "Close Price"
        ],
        row_heights=[0.5, 0.25, 0.25]
    )

    # Portfolio comparison
    fig.add_trace(go.Scatter(
        x=df_bt["time"], y=df_bt["model_portfolio"],
        name="Model Strategy", line=dict(color="blue", width=2)
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df_bt["time"], y=df_bt["buyhold_portfolio"],
        name="Buy & Hold", line=dict(color="orange", width=2, dash="dash")
    ), row=1, col=1)

    # Predictions
    fig.add_trace(go.Scatter(
        x=df_bt["time"], y=df_bt["pred"],
        name="Prediksi", line=dict(color="green", width=1),
        mode="lines"
    ), row=2, col=1)

    # Close price
    fig.add_trace(go.Scatter(
        x=df_bt["time"], y=df_bt["close"],
        name="Close Price", line=dict(color="gray", width=1)
    ), row=3, col=1)

    fig.update_layout(
        height=700,
        title=f"Backtest Results — {ticker}",
        showlegend=True
    )
    fig.show()

# ── Main ─────────────────────────────────────────────────
def run_backtest():
    TICKERS = [
        "BBCA.JK","BBRI.JK","BMRI.JK","TLKM.JK","ASII.JK",
        "GOTO.JK","BYAN.JK","UNVR.JK","ICBP.JK","EMTK.JK"
    ]

    all_metrics = []

    with mlflow.start_run(run_name="Backtest_v1"):
        for ticker in TICKERS:
            try:
                df_bt, metrics = backtest_ticker(ticker)
                all_metrics.append(metrics)
                plot_backtest(df_bt, ticker)
            except Exception as e:
                print(f"ERROR {ticker}: {e}")

        # Summary semua ticker
        df_metrics = pd.DataFrame(all_metrics)
        print(f"\n{'='*60}")
        print("SUMMARY SEMUA TICKER")
        print(f"{'='*60}")
        print(df_metrics.to_string(index=False))

        # Log ke MLflow
        avg_model_return   = df_metrics["model_return"].mean()
        avg_buyhold_return = df_metrics["buyhold_return"].mean()
        avg_sharpe         = df_metrics["sharpe"].mean()
        avg_drawdown       = df_metrics["max_drawdown"].mean()

        mlflow.log_metrics({
            "avg_model_return":   avg_model_return,
            "avg_buyhold_return": avg_buyhold_return,
            "avg_sharpe":         avg_sharpe,
            "avg_max_drawdown":   avg_drawdown,
        })

        print(f"\nAverage Model Return   : {avg_model_return:+.2f}%")
        print(f"Average B&H Return     : {avg_buyhold_return:+.2f}%")
        print(f"Average Sharpe Ratio   : {avg_sharpe:.2f}")
        print(f"Average Max Drawdown   : {avg_drawdown:.2f}%")

        # Simpan metrics ke CSV
        df_metrics.to_csv("models/artifacts/backtest_results.csv", index=False)
        mlflow.log_artifact("models/artifacts/backtest_results.csv")

        print("\nBacktest selesai! Results tersimpan di models/artifacts/backtest_results.csv")

if __name__ == "__main__":
    run_backtest()