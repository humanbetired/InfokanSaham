import yfinance as yf
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

TICKERS = [
    "BBCA.JK","BBRI.JK","BMRI.JK","TLKM.JK","ASII.JK",
    "GOTO.JK","BYAN.JK","UNVR.JK","ICBP.JK","EMTK.JK"
]

def fetch_and_save():
    total = 0
    for ticker in TICKERS:
        try:
            stock = yf.Ticker(ticker)
            news = stock.news

            with engine.connect() as conn:
                for item in news:
                    try:
                        conn.execute(text("""
                            INSERT INTO news_raw (source, ticker, title, content, url, published_at)
                            VALUES (:source, :ticker, :title, :content, :url, :published_at)
                            ON CONFLICT (url) DO NOTHING
                        """), {
                            "source": "Yahoo Finance",
                            "ticker": ticker,
                            "title": item.get("title", ""),
                            "content": item.get("summary", ""),
                            "url": item.get("link", ""),
                            "published_at": datetime.utcfromtimestamp(item.get("providerPublishTime", 0)),
                        })
                        total += 1
                    except:
                        pass
                conn.commit()
            print(f"{ticker}: {len(news)} news")
        except Exception as e:
            print(f"ERROR {ticker}: {e}")

    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO pipeline_log (source, status, rows_fetched)
            VALUES ('yfinance_news', 'success', :rows)
        """), {"rows": total})
        conn.commit()

    print(f"\nYFinance News selesai: {total} rows total")

if __name__ == "__main__":
    fetch_and_save()