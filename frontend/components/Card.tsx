export default function Card({
  children,
  className = "",
  style = {},
}: {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}) {
  return (
    <div className={className} style={{
      background: "var(--surface)",
      border: "1px solid var(--border)",
      borderRadius: "12px",
      padding: "20px",
      boxShadow: "0 1px 3px rgba(5,15,26,0.06)",
      ...style,
    }}>
      {children}
    </div>
  );
}