from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import pandas as pd
from api.dependencies import get_engine

router = APIRouter(prefix="/backtest", tags=["Backtest"])

class BacktestResult(BaseModel):
    ticker: str
    model_return: float
    buyhold_return: float
    sharpe: float
    max_drawdown: float
    win_rate: float
    total_trades: int

@router.get("/results", response_model=List[BacktestResult])
def get_backtest_results():
    try:
        df = pd.read_csv("models/artifacts/backtest_results.csv")
        return df.to_dict(orient="records")
    except:
        return []

@router.get("/summary")
def get_backtest_summary():
    try:
        df = pd.read_csv("models/artifacts/backtest_results.csv")
        return {
            "avg_model_return":   round(df["model_return"].mean(), 2),
            "avg_buyhold_return": round(df["buyhold_return"].mean(), 2),
            "avg_sharpe":         round(df["sharpe"].mean(), 2),
            "avg_max_drawdown":   round(df["max_drawdown"].mean(), 2),
            "best_ticker":        df.loc[df["model_return"].idxmax(), "ticker"],
            "worst_ticker":       df.loc[df["model_return"].idxmin(), "ticker"],
            "outperform_count":   int((df["model_return"] > df["buyhold_return"]).sum()),
            "total_tickers":      len(df),
        }
    except:
        return {}