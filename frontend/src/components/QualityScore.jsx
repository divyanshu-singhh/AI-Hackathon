export default function QualityScore({ score }) {
  const normalized = typeof score === "number" ? score : null;
  const label = normalized === null ? "N/A" : `${normalized}`;
  const className = normalized === null ? "muted" : normalized >= 80 ? "good" : normalized >= 60 ? "average" : "poor";

  return (
    <div className={`quality ${className}`}>
      <div className="quality-ring" style={{ "--score": normalized || 0 }}>
        <span>{label}</span>
      </div>
      <strong>Quality</strong>
    </div>
  );
}
