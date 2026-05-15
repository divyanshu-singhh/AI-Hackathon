import { Info } from "lucide-react";
import ImageCompare from "./ImageCompare.jsx";
import QualityScore from "./QualityScore.jsx";

export default function BatchPreviewGrid({ results = [] }) {
  const visible = results.filter((item) => item.status === "success").slice(0, 5);
  if (!visible.length) {
    return null;
  }

  return (
    <section className="batch-preview-section">
      <div className="table-header">
        <div>
          <h2>Image Comparisons</h2>
          <p className="muted">Showing up to 5 processed images.</p>
        </div>
      </div>
      <div className="batch-preview-grid">
        {visible.map((result) => (
          <article className="batch-preview-card" key={result.image_id}>
            <div className="batch-card-head">
              <div>
                <h3>{result.file_name}</h3>
                <p className="muted">{result.category || "Uncategorized"}</p>
              </div>
              <div className="quality-card-actions">
                <QualityScore score={result.quality_score} />
                <QualityInfo breakdown={result.quality_breakdown} />
              </div>
            </div>
            <ImageCompare result={result} />
            <div className="batch-card-meta">
              {(result.tags || []).slice(0, 5).map((tag) => <span key={tag}>{tag}</span>)}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function QualityInfo({ breakdown }) {
  const deductions = breakdown?.deductions || [];
  return (
    <button className="quality-info compact-info" type="button" aria-label="Quality explanation">
      <Info size={16} />
      <span className="quality-popover">
        <b>Why Not 100?</b>
        {deductions.length ? (
          deductions.map((item) => (
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
  );
}
