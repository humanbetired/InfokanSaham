export default function Chip({
  value,
  suffix = "%",
}: {
  value: number;
  suffix?: string;
}) {
  const positive = value > 0;
  const neutral  = value === 0;

  return (
    <span className={
      neutral ? "chip-neutral" : positive ? "chip-positive" : "chip-negative"
    } style={{
      padding: "2px 10px",
      borderRadius: "6px",
      fontSize: "13px",
      fontWeight: 500,
      fontFamily: "JetBrains Mono, monospace",
    }}>
      {positive ? "+" : ""}{value.toFixed(2)}{suffix}
    </span>
  );
}