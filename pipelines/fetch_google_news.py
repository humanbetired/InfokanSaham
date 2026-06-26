import feedparser
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime
import os, time

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

QUERIES = [
    ("BBCA", "BBCA Bank BCA saham"),
    ("BBRI", "BBRI Bank BRI saham"),
    ("BMRI", "BMRI Bank Mandiri saham"),
    ("TLKM", "TLKM Telkom Indonesia saham"),
    ("ASII", "ASII Astra International saham"),
    ("GOTO", "GOTO GoTo Gojek Tokopedia saham"),
    ("BYAN", "BYAN Bayan Resources saham"),
    ("UNVR", "UNVR Unilever Indonesia saham"),
    ("ICBP", "ICBP Indofood saham"),
    ("EMTK", "EMTK Emtek saham"),
]

def fetch_google_news():
    total = 0
    for ticker, query in QUERIES:
        try:
            # Google News RSS feed
            url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=id&gl=ID&ceid=ID:id"
            feed = feedparser.parse(url)

            with engine.connect() as conn:
                for entry in feed.entries:
                    try:
                        published = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now()
                        conn.execute(text("""
                            INSERT INTO news_raw (source, ticker, title, content, url, published_at)
                            VALUES (:source, :ticker, :title, :content, :url, :published_at)
                            ON CONFLICT (url) DO NOTHING
                        """), {
                            "source": "Google News",
                            "ticker": ticker,
                            "title": entry.title,
                            "content": entry.get("summary", ""),
                            "url": entry.link,
                            "published_at": published,
                        })
                        total += 1
                    except:
                        pass
                conn.commit()

            print(f"{ticker}: {len(feed.entries)} articles")
            time.sleep(1)  
        except Exception as e:
            print(f"ERROR {ticker}: {e}")

    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO pipeline_log (source, status, rows_fetched)
            VALUES ('google_news', 'success', :rows)
        """), {"rows": total})
        conn.commit()

    print(f"\nGoogle News selesai: {total} rows total")

if __name__ == "__main__":
    fetch_google_news()