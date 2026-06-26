"use client";
import { useState, useEffect } from "react";
import { marketAPI, predictAPI, PredictResponse } from "@/lib/api";
import Card from "@/components/Card";

export default function PredictPage() {
  const [tickers, setTickers]   = useState<string[]>([]);
  const [ticker, setTicker]     = useState("BBCA.JK");
  const [news, setNews]         = useState("");
  const [result, setResult]     = useState<PredictResponse | null>(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");

  useEffect(() => {
    marketAPI.getTickers().then(r => setTickers(r.data.tickers));
  }, []);

  const handlePredict = async () => {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const r = await predictAPI.predict(ticker, news || "market neutral");
      setResult(r.data);
    } catch {
      setError("Gagal mendapatkan prediksi. Pastikan API server berjalan.");
    } finally {
      setLoading(false);
    }
  };

  const recColor = result?.recommendation.includes("BUY")  ? "var(--success)" :
                   result?.recommendation.includes("SELL") ? "var(--error)"   : "var(--warning)";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px", maxWidth: "680px" }}>

      <div>
        <h1 style={{ fontSize: "32px", fontWeight: 700, letterSpacing: "-0.02em", marginBottom: "4px" }}>
          Prediksi AI
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "14px" }}>
          Gabungan sinyal LSTM + FinBERT untuk prediksi arah harga besok
        </p>
      </div>

      <Card>
        {/* Ticker Select */}
        <div style={{ marginBottom: "16px" }}>
          <label style={{ fontSize: "14px", fontWeight: 500, display: "block", marginBottom: "6px" }}>
            Pilih Saham
          </label>
          <select value={ticker} onChange={e => setTicker(e.target.value)}
            style={{
              width: "100%", height: "44px", padding: "0 14px",
              borderRadius: "8px", border: "1px solid var(--border)",
              fontSize: "15px", fontFamily: "DM Sans, sans-serif",
              background: "var(--surface)", color: "var(--text-primary)",
              outline: "none", cursor: "pointer",
            }}>
            {tickers.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>

        {/* News Input */}
        <div style={{ marginBottom: "20px" }}>
          <label style={{ fontSize: "14px", fontWeight: 500, display: "block", marginBottom: "6px" }}>
            Berita Terkini (opsional)
          </label>
          <textarea value={news} onChange={e => setNews(e.target.value)}
            placeholder="Contoh: Bank BCA catat laba tertinggi semester ini..."
            rows={3}
            style={{
              width: "100%", padding: "10px 14px",
              borderRadius: "8px", border: "1px solid var(--border)",
              fontSize: "15px", fontFamily: "DM Sans, sans-serif",
              resize: "vertical", outline: "none", boxSizing: "border-box",
            }}
          />
        </div>

        {/* Button */}
        <button onClick={handlePredict} disabled={loading}
          style={{
            width: "100%", height: "44px",
            background: loading ? "var(--neutral)" : "var(--primary)",
            color: "white", border: "none", borderRadius: "8px",
            fontSize: "15px", fontWeight: 700, cursor: loading ? "not-allowed" : "pointer",
            transition: "background 0.2s",
          }}>
          {loading ? "Menganalisis..." : "Prediksi Sekarang"}
        </button>

        {error && (
          <p style={{ color: "var(--error)", fontSize: "14px", marginTop: "12px" }}>{error}</p>
        )}
      </Card>

      {/* Result */}
      {result && (
        <Card style={{ border: `2px solid ${recColor}` }}>
          <div style={{ textAlign: "center", marginBottom: "24px" }}>
            <p style={{ fontSize: "14px", color: "var(--text-secondary)", marginBottom: "8px" }}>
              Rekomendasi untuk {result.ticker}
            </p>
            <p style={{ fontSize: "40px", fontWeight: 700, color: recColor }}>
              {result.recommendation}
            </p>
            <p className="mono" style={{ fontSize: "16px", color: "var(--text-secondary)", marginTop: "4px" }}>
              Confidence: {(result.confidence * 100).toFixed(1)}%
            </p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            {[
              { label: "Prediksi Arah",    value: result.prediction,
                color: result.prediction === "NAIK" ? "var(--success)" : "var(--error)" },
              { label: "LSTM Probability", value: `${(result.lstm_proba * 100).toFixed(1)}%`,
                color: "var(--primary)" },
              { label: "Sentiment Score",  value: result.sentiment_score.toFixed(4),
                color: result.sentiment_score > 0 ? "var(--success)" : "var(--error)" },
              { label: "Confidence",       value: `${(result.confidence * 100).toFixed(1)}%`,
                color: "var(--text-primary)" },
            ].map(item => (
              <div key={item.label} style={{
                background: "var(--background)", borderRadius: "8px", padding: "12px 16px"
              }}>
                <p style={{ fontSize: "12px", color: "var(--neutral)", fontWeight: 500,
                  textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "4px" }}>
                  {item.label}
                </p>
                <p className="mono" style={{ fontSize: "18px", fontWeight: 700, color: item.color }}>
                  {item.value}
                </p>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}