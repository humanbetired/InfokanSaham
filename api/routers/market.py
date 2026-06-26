from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import pandas as pd
from api.dependencies import get_engine

router = APIRouter(prefix="/market", tags=["Market Data"])

class OHLCVPoint(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    rsi: float = None
    macd: float = None

class TickerSummary(BaseModel):
    ticker: str
    last_close: float
    change_pct: float
    volume: float
    rsi: float
    trend: str

@router.get("/tickers")
def get_tickers():
    engine = get_engine()
    result = pd.read_sql("SELECT DISTINCT ticker FROM ohlcv ORDER BY ticker", engine)
    return {"tickers": result["ticker"].tolist()}

@router.get("/ohlcv/{ticker}", response_model=List[OHLCVPoint])
def get_ohlcv(ticker: str, limit: int = 100):
    engine = get_engine()
    df = pd.read_sql(f"""
        SELECT time, open, high, low, close, volume
        FROM ohlcv
        WHERE ticker = '{ticker}'
        ORDER BY time DESC
        LIMIT {limit}
    """, engine)

    if df.empty:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker} tidak ditemukan")

    df = df.sort_values("time")
    df["time"] = df["time"].astype(str)
    return df.to_dict(orient="records")

@router.get("/summary", response_model=List[TickerSummary])
def get_summary():
    engine = get_engine()
    tickers = pd.read_sql(
        "SELECT DISTINCT ticker FROM ohlcv ORDER BY ticker", engine
    )["ticker"].tolist()

    summaries = []
    for ticker in tickers:
        df = pd.read_sql(f"""
            SELECT time, close, volume, rsi
            FROM ohlcv_featured
            WHERE ticker = '{ticker}'
            ORDER BY time DESC
            LIMIT 2
        """, engine)

        if len(df) < 2:
            continue

        last  = df.iloc[0]
        prev  = df.iloc[1]
        chg   = (last["close"] - prev["close"]) / prev["close"] * 100
        trend = "BULLISH" if chg > 0 else "BEARISH"

        summaries.append(TickerSummary(
            ticker=ticker,
            last_close=round(float(last["close"]), 2),
            change_pct=round(float(chg), 2),
            volume=round(float(last["volume"]), 0),
            rsi=round(float(last["rsi"]) if last["rsi"] else 0, 2),
            trend=trend,
        ))

    return summaries