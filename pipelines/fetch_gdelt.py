import requests, zipfile, io
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

COLS = {
    0: "event_id", 1: "event_date", 5: "actor1", 10: "actor2",
    26: "event_code", 30: "goldstein", 31: "num_mentions",
    34: "avg_tone", 57: "source_url"
}

def fetch_and_save():
    try:
        r = requests.get("http://data.gdeltproject.org/gdeltv2/lastupdate.txt")
        export_url = [l for l in r.text.strip().split("\n") if "export" in l][0].split()[-1]

        print(f"  Downloading GDELT: {export_url}")
        r2 = requests.get(export_url)
        z = zipfile.ZipFile(io.BytesIO(r2.content))

        with z.open(z.namelist()[0]) as f:
            df_raw = pd.read_csv(f, sep="\t", header=None, low_memory=False)

        df = df_raw[[int(k) for k in COLS.keys()]].copy()
        df.columns = list(COLS.values())

        df["source_url"] = df["source_url"].astype(str)
        mask = df["source_url"].str.contains(
            "indonesia|finance|stock|market|economy|saham|bursa|asia|jakarta|idx",
            case=False, na=False
        )
        df = df[mask].copy()
        df["event_date"] = pd.to_datetime(df["event_date"], format="%Y%m%d", errors="coerce")
        df.dropna(subset=["event_date"], inplace=True)

        total = 0
        with engine.connect() as conn:
            for _, row in df.iterrows():
                try:
                    conn.execute(text("""
                        INSERT INTO gdelt_raw
                        (event_id, event_date, actor1, actor2, event_code,
                         goldstein, num_mentions, avg_tone, source_url)
                        VALUES (:event_id, :event_date, :actor1, :actor2, :event_code,
                                :goldstein, :num_mentions, :avg_tone, :source_url)
                        ON CONFLICT (event_id) DO NOTHING
                    """), row.to_dict())
                    total += 1
                except:
                    pass
            conn.commit()

        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO pipeline_log (source, status, rows_fetched)
                VALUES ('gdelt', 'success', :rows)
            """), {"rows": total})
            conn.commit()

        print(f"\nGDELT selesai: {total} rows total")
    except Exception as e:
        print(f"\nGDELT ERROR: {e}")

if __name__ == "__main__":
    fetch_and_save()