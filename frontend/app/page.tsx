"use client";
import { useEffect, useState } from "react";
import { marketAPI, backtestAPI, TickerSummary, BacktestSummary } from "@/lib/api";
import Card from "@/components/Card";
import Chip from "@/components/Chip";
import Skeleton from "@/components/Skeleton";

export default function Dashboard() {
  const [summary, setSummary]   = useState<TickerSummary[]>([]);
  const [backtest, setBacktest] = useState<BacktestSummary | null>(null);
  const [loading, setLoading]   = useState(true);

  useEffect(() => {
    Promise.all([
      marketAPI.getSummary(),
      backtestAPI.getSummary(),
    ]).then(([s, b]) => {
      setSummary(s.data);
      setBacktest(b.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>

      {/* Header */}
      <div>
        <h1 style={{ fontSize: "32px", fontWeight: 700, letterSpacing: "-0.02em", marginBottom: "4px" }}>
          Market Overview
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "14px" }}>
          Stock intelligence IDX
        </p>
      </div>

      {/* Stats Row */}
      {backtest && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "16px" }}>
          {[
            { label: "Avg Model Return",   value: `+${backtest.avg_model_return}%`,   color: "var(--success)" },
            { label: "Avg B&H Return",     value: `+${backtest.avg_buyhold_return}%`, color: "var(--text-primary)" },
            { label: "Avg Sharpe Ratio",   value: backtest.avg_sharpe.toFixed(2),     color: "var(--primary)" },
            { label: "Outperform B&H",     value: `${backtest.outperform_count}/10`,  color: "var(--success)" },
          ].map(stat => (
            <Card key={stat.label}>
              <p style={{ fontSize: "12px", fontWeight: 500, color: "var(--neutral)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "8px" }}>
                {stat.label}
              </p>
              <p className="mono" style={{ fontSize: "24px", fontWeight: 700, color: stat.color }}>
                {stat.value}
              </p>
            </Card>
          ))}
        </div>
      )}

      {/* Market Table */}
      <Card>
        <h2 style={{ fontSize: "18px", fontWeight: 700, marginBottom: "16px" }}>
          Daftar Saham IDX
        </h2>

        {/* Table Header */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "2fr 1fr 1fr 1fr 1fr 1fr",
          padding: "8px 16px",
          borderBottom: "1px solid var(--border)",
        }}>
          {["TICKER", "HARGA", "PERUBAHAN", "VOLUME", "RSI", "TREND"].map(h => (
            <span key={h} style={{
              fontSize: "12px", fontWeight: 500,
              color: "var(--neutral)", textTransform: "uppercase",
              letterSpacing: "0.06em",
              textAlign: h === "TICKER" ? "left" : "right",
            }}>{h}</span>
          ))}
        </div>

        {/* Table Rows */}
        {loading ? (
          Array.from({length: 5}).map((_, i) => (
            <div key={i} style={{ padding: "16px", borderBottom: "1px solid var(--border)" }}>
              <Skeleton height="20px" />
            </div>
          ))
        ) : summary.map(row => (
          <div key={row.ticker} style={{
            display: "grid",
            gridTemplateColumns: "2fr 1fr 1fr 1fr 1fr 1fr",
            padding: "16px",
            borderBottom: "1px solid var(--border)",
            alignItems: "center",
            cursor: "pointer",
            transition: "background 0.15s",
          }}
          onMouseEnter={e => (e.currentTarget.style.background = "var(--background)")}
          onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
          onClick={() => window.location.href = `/ticker?t=${row.ticker}`}
          >
            <span style={{ fontWeight: 700, color: "var(--text-primary)" }}>
              {row.ticker}
            </span>
            <span className="mono" style={{ textAlign: "right", fontWeight: 500 }}>
              {row.last_close.toLocaleString("id-ID")}
            </span>
            <div style={{ textAlign: "right" }}>
              <Chip value={row.change_pct} />
            </div>
            <span className="mono" style={{ textAlign: "right", color: "var(--text-secondary)", fontSize: "13px" }}>
              {(row.volume / 1_000_000).toFixed(1)}M
            </span>
            <span className="mono" style={{
              textAlign: "right",
              color: row.rsi > 70 ? "var(--error)" : row.rsi < 30 ? "var(--success)" : "var(--text-primary)",
              fontWeight: 500,
            }}>
              {row.rsi.toFixed(1)}
            </span>
            <span style={{ textAlign: "right", fontSize: "13px" }}>
              {row.trend}
            </span>
          </div>
        ))}
      </Card>
    </div>
  );
}