"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/",          label: "Dashboard"  },
  { href: "/ticker",    label: "Ticker"     },
  { href: "/predict",   label: "Prediksi"   },
  { href: "/backtest",  label: "Backtest"   },
];

export default function Navbar() {
  const path = usePathname();

  return (
    <nav style={{
      height: "60px",
      background: "var(--surface)",
      borderBottom: "1px solid var(--border)",
      display: "flex",
      alignItems: "center",
      padding: "0 24px",
      justifyContent: "space-between",
      boxShadow: "0 1px 3px rgba(5,15,26,0.06)",
    }}>
      {/* Logo */}
      <div style={{
        fontWeight: 700,
        fontSize: "20px",
        color: "var(--secondary)",
        letterSpacing: "-0.02em",
      }}>
        InfokanSaham
      </div>

      {/* Nav Links */}
      <div style={{ display: "flex", gap: "32px" }}>
        {links.map(link => {
          const active = path === link.href;
          return (
            <Link key={link.href} href={link.href} style={{
              fontWeight: 500,
              fontSize: "15px",
              color: active ? "var(--primary)" : "var(--text-secondary)",
              textDecoration: "none",
              borderBottom: active ? "2px solid var(--primary)" : "2px solid transparent",
              paddingBottom: "4px",
              transition: "color 0.2s",
            }}>
              {link.label}
            </Link>
          );
        })}
      </div>

      {/* Badge */}
      <div style={{
        background: "var(--primary)",
        color: "white",
        borderRadius: "8px",
        padding: "8px 16px",
        fontSize: "13px",
        fontWeight: 700,
      }}>
        IDX Market
      </div>
    </nav>
  );
}