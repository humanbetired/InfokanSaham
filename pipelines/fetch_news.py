import requests
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
API_KEY = os.getenv("NEWS_API_KEY")

QUERIES = [
    ("BBCA", "BCA Bank Indonesia"),
    ("BBRI", "BRI Bank Indonesia"),
    ("BMRI", "Bank Mandiri Indonesia"),
    ("TLKM", "Telkom Indonesia"),
    ("ASII", "Astra International Indonesia"),
    ("GOTO", "GoTo Gojek Tokopedia"),
    ("BYAN", "Bayan Resources coal Indonesia"),
    ("UNVR", "Unilever Indonesia"),
    ("ICBP", "Indofood Indonesia"),
    ("EMTK", "Emtek Indonesia"),
]

def fetch_and_save(days_back=7):
    total = 0
    from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    for ticker, query in QUERIES:
        try:
            r = requests.get("https://newsapi.org/v2/everything", params={
                "q": query,
                "sortBy": "publishedAt",
                "language": "en",
                "apiKey": API_KEY,
                "pageSize": 100,
            })
            print(f"  API Response: {r.json()}")
            articles = r.json().get("articles", [])

            with engine.connect() as conn:
                for a in articles:
                    try:
                        conn.execute(text("""
                            INSERT INTO news_raw (source, ticker, title, content, url, published_at)
                            VALUES (:source, :ticker, :title, :content, :url, :published_at)
                            ON CONFLICT (url) DO NOTHING
                        """), {
                            "source": a["source"]["name"],
                            "ticker": ticker,
                            "title": a["title"],
                            "content": a.get("content", ""),
                            "url": a["url"],
                            "published_at": a["publishedAt"],
                        })
                        total += 1
                    except:
                        pass
                conn.commit()
            print(f"{ticker}: {len(articles)} articles")
        except Exception as e:
            print(f"ERROR {ticker}: {e}")

    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO pipeline_log (source, status, rows_fetched)
            VALUES ('news', 'success', :rows)
        """), {"rows": total})
        conn.commit()

    print(f"\nNews selesai: {total} rows total")

if __name__ == "__main__":
    fetch_and_save()