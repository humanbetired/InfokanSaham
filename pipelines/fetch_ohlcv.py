import yfinance as yf
from sqlalchemy import create_engine, text
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

TICKERS = [
    "BBCA.JK",  # Bank BCA
    "BBRI.JK",  # Bank BRI
    "BMRI.JK",  # Bank Mandiri
    "TLKM.JK",  # Telkom Indonesia
    "ASII.JK",  # Astra International
    "GOTO.JK",  # GoTo
    "BYAN.JK",  # Bayan Resources
    "UNVR.JK",  # Unilever Indonesia
    "ICBP.JK",  # Indofood CBP
    "EMTK.JK",  # Elang Mahkota Teknologi
]

def fetch_and_save(period="5y"):
    total = 0
    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period=period, interval="1d", auto_adjust=True)
            df = df.reset_index()
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [c[0].lower() for c in df.columns]
            else:
                df.columns = [c.lower() for c in df.columns]
            df = df.rename(columns={"date": "time"})
            df["ticker"] = ticker
            df = df[["time","ticker","open","high","low","close","volume"]].dropna()

            with engine.connect() as conn:
                for _, row in df.iterrows():
                    conn.execute(text("""
                        INSERT INTO ohlcv (time, ticker, open, high, low, close, volume)
                        VALUES (:time, :ticker, :open, :high, :low, :close, :volume)
                        ON CONFLICT (time, ticker) DO NOTHING
                    """), row.to_dict())
                conn.commit()

            total += len(df)
            print(f"{ticker}: {len(df)} rows")
        except Exception as e:
            print(f"ERROR {ticker}: {e}")

    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO pipeline_log (source, status, rows_fetched)
            VALUES ('ohlcv', 'success', :rows)
        """), {"rows": total})
        conn.commit()

    print(f"\nOHLCV selesai: {total} rows total")

if __name__ == "__main__":
    fetch_and_save()