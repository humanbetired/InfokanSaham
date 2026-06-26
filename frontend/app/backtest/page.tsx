"use client";
import { useEffect, useState } from "react";
import { backtestAPI, BacktestResult, BacktestSummary } from "@/lib/api";
import Card from "@/components/Card";
import Chip from "@/components/Chip";
import Skeleton from "@/components/Skeleton";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from "recharts";

export default function BacktestPage() {
  const [results, setResults]   = useState<BacktestResult[]>([]);
  const [summary, setSummary]   = useState<BacktestSummary | null>(null);
  const [loading, setLoading]   = useState(true);

  useEffect(() => {
    Promise.all([
      backtestAPI.getResults(),
      backtestAPI.getSummary(),
    ]).then(([r, s]) => {
      setResults(r.data);
      setSummary(s.data);
      setLoading(false);
    });
  }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>

      <div>
        <h1 style={{ fontSize: "32px", fontWeight: 700, letterSpacing: "-0.02em", marginBottom: "4px" }}>
          Hasil Backtesting
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "14px" }}>
          Simulasi performa model vs strategi Buy & Hold selama 2 tahun
        </p>
      </div>

      {/* Summary Stats */}
      {summary && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "16px" }}>
          {[
            { label: "Avg Model Return",   value: `+${summary.avg_model_return}%`,   color: "var(--success)" },
            { label: "Avg B&H Return",     value: `+${summary.avg_buyhold_return}%`, color: "var(--text-primary)" },
            { label: "Best Ticker",        value: summary.best_ticker,               color: "var(--primary)" },
            { label: "Outperform B&H",     value: `${summary.outperform_count}/10`,  color: "var(--success)" },
          ].map(s => (
            <Card key={s.label}>
              <p style={{ fontSize: "12px", fontWeight: 500, color: "var(--neutral)",
                textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "8px" }}>
                {s.label}
              </p>
              <p className="mono" style={{ fontSize: "22px", fontWeight: 700, color: s.color }}>
                {s.value}
              </p>
            </Card>
          ))}
        </div>
      )}

      {/* Bar Chart */}
      <Card>
        <h3 style={{ fontSize: "16px", fontWeight: 700, marginBottom: "16px" }}>
          Model Return vs Buy & Hold per Ticker
        </h3>
        {loading ? <Skeleton height="300px" /> : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={results} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="ticker" tick={{ fontSize: 11, fill: "var(--neutral)" }}
                tickFormatter={t => t.replace(".JK", "")} />
              <YAxis tick={{ fontSize: 11, fill: "var(--neutral)" }}
                tickFormatter={v => `${v}%`} />
              <Tooltip formatter={(v: number) => [`${v.toFixed(2)}%`]}
                contentStyle={{ borderRadius: "8px", border: "1px solid var(--border)" }} />
              <Legend />
              <Bar dataKey="model_return"   name="Model Strategy" fill="#0052FF" radius={[4,4,0,0]} />
              <Bar dataKey="buyhold_return" name="Buy & Hold"      fill="#8A919E" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </Card>

      {/* Detail Table */}
      <Card>
        <h3 style={{ fontSize: "16px", fontWeight: 700, marginBottom: "16px" }}>
          Detail Per Ticker
        </h3>

        {/* Header */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "1.5fr 1fr 1fr 1fr 1fr 1fr 1fr",
          padding: "8px 16px",
          borderBottom: "1px solid var(--border)",
        }}>
          {["TICKER","MODEL RETURN","B&H RETURN","SHARPE","MAX DD","WIN RATE","TRADES"].map(h => (
            <span key={h} style={{
              fontSize: "11px", fontWeight: 500, color: "var(--neutral)",
              textTransform: "uppercase", letterSpacing: "0.06em",
              textAlign: h === "TICKER" ? "left" : "right",
            }}>{h}</span>
          ))}
        </div>

        {loading ? (
          Array.from({length: 5}).map((_, i) => (
            <div key={i} style={{ padding: "16px", borderBottom: "1px solid var(--border)" }}>
              <Skeleton height="20px" />
            </div>
          ))
        ) : results.map(row => (
          <div key={row.ticker} style={{
            display: "grid",
            gridTemplateColumns: "1.5fr 1fr 1fr 1fr 1fr 1fr 1fr",
            padding: "16px", borderBottom: "1px solid var(--border)",
            alignItems: "center",
          }}>
            <span style={{ fontWeight: 700 }}>{row.ticker}</span>
            <div style={{ textAlign: "right" }}>
              <Chip value={row.model_return} />
            </div>
            <div style={{ textAlign: "right" }}>
              <Chip value={row.buyhold_return} />
            </div>
            <span className="mono" style={{
              textAlign: "right", fontSize: "14px",
              color: row.sharpe > 1 ? "var(--success)" : row.sharpe > 0 ? "var(--text-primary)" : "var(--error)",
            }}>
              {row.sharpe.toFixed(2)}
            </span>
            <span className="mono" style={{ textAlign: "right", fontSize: "14px", color: "var(--error)" }}>
              {row.max_drawdown.toFixed(1)}%
            </span>
            <span className="mono" style={{ textAlign: "right", fontSize: "14px" }}>
              {row.win_rate.toFixed(1)}%
            </span>
            <span className="mono" style={{ textAlign: "right", fontSize: "14px", color: "var(--text-secondary)" }}>
              {row.total_trades}
            </span>
          </div>
        ))}
      </Card>
    </div>
  );
}