"use client";
import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { marketAPI, OHLCVPoint } from "@/lib/api";
import Card from "@/components/Card";
import Skeleton from "@/components/Skeleton";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, BarChart, Bar,
} from "recharts";

function TickerContent() {
  const params  = useSearchParams();
  const ticker  = params.get("t") || "BBCA.JK";
  const [data, setData]     = useState<OHLCVPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    marketAPI.getOHLCV(ticker, 60).then(r => {
      setData(r.data);
      setLoading(false);
    });
  }, [ticker]);

  const last    = data[data.length - 1];
  const prev    = data[data.length - 2];
  const change  = last && prev ? ((last.close - prev.close) / prev.close * 100) : 0;
  const isUp    = change >= 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>

      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
        <div>
          <h1 style={{ fontSize: "32px", fontWeight: 700, letterSpacing: "-0.02em" }}>
            {ticker}
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "14px" }}>
            IDX — Data 60 hari terakhir
          </p>
        </div>
        {last && (
          <div style={{ marginLeft: "auto", textAlign: "right" }}>
            <p className="mono" style={{ fontSize: "32px", fontWeight: 700 }}>
              {last.close.toLocaleString("id-ID")}
            </p>
            <p className="mono" style={{
              fontSize: "16px",
              color: isUp ? "var(--success)" : "var(--error)",
              fontWeight: 500,
            }}>
              {isUp ? "▲" : "▼"} {Math.abs(change).toFixed(2)}%
            </p>
          </div>
        )}
      </div>

      {/* Price Chart */}
      <Card>
        <h3 style={{ fontSize: "16px", fontWeight: 700, marginBottom: "16px" }}>
          Grafik Harga Penutupan
        </h3>
        {loading ? <Skeleton height="250px" /> : (
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={data}>
              <defs>
                <linearGradient id="colorClose" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#0052FF" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#0052FF" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="time" tick={{ fontSize: 11, fill: "var(--neutral)" }}
                tickFormatter={v => v.slice(5, 10)} />
              <YAxis tick={{ fontSize: 11, fill: "var(--neutral)" }}
                tickFormatter={v => v.toLocaleString("id-ID")} width={80} />
              <Tooltip
                formatter={(v: number) => [v.toLocaleString("id-ID"), "Close"]}
                labelFormatter={l => `Tanggal: ${l}`}
                contentStyle={{ borderRadius: "8px", border: "1px solid var(--border)" }}
              />
              <Area type="monotone" dataKey="close"
                stroke="#0052FF" strokeWidth={2}
                fill="url(#colorClose)" />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </Card>

      {/* Volume Chart */}
      <Card>
        <h3 style={{ fontSize: "16px", fontWeight: 700, marginBottom: "16px" }}>
          Volume Perdagangan
        </h3>
        {loading ? <Skeleton height="150px" /> : (
          <ResponsiveContainer width="100%" height={150}>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="time" tick={{ fontSize: 11, fill: "var(--neutral)" }}
                tickFormatter={v => v.slice(5, 10)} />
              <YAxis tick={{ fontSize: 11, fill: "var(--neutral)" }}
                tickFormatter={v => `${(v/1e6).toFixed(0)}M`} width={60} />
              <Tooltip
                formatter={(v: number) => [`${(v/1e6).toFixed(2)}M`, "Volume"]}
                contentStyle={{ borderRadius: "8px", border: "1px solid var(--border)" }}
              />
              <Bar dataKey="volume" fill="#0052FF" opacity={0.7} radius={[2,2,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </Card>
    </div>
  );
}

export default function TickerPage() {
  return (
    <Suspense fallback={<Skeleton height="400px" />}>
      <TickerContent />
    </Suspense>
  );
}