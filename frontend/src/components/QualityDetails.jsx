import { Info } from "lucide-react";

export default function QualityDetails({ breakdown }) {
  if (!breakdown || !Object.keys(breakdown).length) {
    return null;
  }

  const metrics = [
    ["Resolution", `${breakdown.width || "-"} x ${breakdown.height || "-"}`, breakdown.resolution_ok ? "Good" : "Needs work"],
    ["Blur", value(breakdown.blur_score), scoreLabel(breakdown.blur_score, 80, 40)],
    ["Brightness", value(breakdown.brightness), rangeLabel(breakdown.brightness, 80, 220)],
    ["Contrast", value(breakdown.contrast), scoreLabel(breakdown.contrast, 35, 20)],
    ["Noise", value(breakdown.noise_score), inverseLabel(breakdown.noise_score, 18)],
    ["Background", value(breakdown.background_complexity, 4), inverseLabel(breakdown.background_complexity, 0.18)]
  ];

  return (
    <section className="quality-details">
      <div className="quality-details-header">
        <div>
          <h3>Quality Breakdown</h3>
        </div>
        <div className="quality-score-inline">
          <strong>{breakdown.quality_score ?? "-"} / 100</strong>
          <button className="quality-info" type="button" aria-label="Why not 100">
            <Info size={17} />
            <span className="quality-popover">
              <b>Why Not 100?</b>
              {breakdown.deductions?.length ? (
                breakdown.deductions.map((item) => (
                  <em key={`${item.metric}-${item.reason}`}>
                    -{item.points} {item.metric}
                    <small>{item.reason}</small>
                    <small>{item.suggestion}</small>
                  </em>
                ))
              ) : (
                <em>No quality deductions found.</em>
              )}
            </span>
          </button>
        </div>
      </div>

      <div className="quality-metrics">
        {metrics.map(([label, metricValue, status]) => (
          <div className="metric-card" key={label}>
            <span>{label}</span>
            <strong>{metricValue}</strong>
            <em>{status}</em>
          </div>
        ))}
      </div>

    </section>
  );
}

function value(input, digits = 2) {
  return typeof input === "number" ? input.toFixed(digits) : "-";
}

function scoreLabel(input, good, poor) {
  if (typeof input !== "number") return "Not checked";
  if (input >= good) return "Good";
  if (input >= poor) return "Average";
  return "Needs work";
}

function inverseLabel(input, limit) {
  if (typeof input !== "number") return "Not checked";
  return input <= limit ? "Good" : "Needs work";
}

function rangeLabel(input, low, high) {
  if (typeof input !== "number") return "Not checked";
  if (input < low) return "Too low";
  if (input > high) return "Too high";
  return "Good";
}
