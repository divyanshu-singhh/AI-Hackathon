import ImageCompare from "./ImageCompare.jsx";
import QualityScore from "./QualityScore.jsx";

export default function ResultCard({ result }) {
  if (!result) {
    return (
      <section className="result-placeholder">
        <h2>Waiting for an image</h2>
        <p>Processed outputs will appear here.</p>
      </section>
    );
  }

  return (
    <section className="result-card">
      <div className="result-topline">
        <div>
          <p className={`status ${result.status}`}>{result.status}</p>
          <h2>{result.seo_title || result.main_product || result.file_name}</h2>
          <p className="muted">{result.category || "Uncategorized"}</p>
        </div>
        <QualityScore score={result.quality_score} />
      </div>

      <ImageCompare result={result} />

      <div className="metadata-grid">
        <InfoBlock title="Objects" items={result.detected_objects} empty="No objects detected" />
        <InfoBlock title="Tags" items={result.tags} empty="No tags generated" isBadge />
      </div>

      {result.extracted_text ? (
        <div className="text-block">
          <h3>Extracted Text</h3>
          <p>{result.extracted_text}</p>
        </div>
      ) : null}

      <div className="metadata-grid">
        <InfoBlock title="Issues" items={result.issues} empty="No issues found" />
        <InfoBlock title="Suggestions" items={result.suggestions} empty="No suggestions" />
      </div>

      {result.error ? <p className="error-line">{result.error}</p> : null}
    </section>
  );
}

function InfoBlock({ title, items = [], empty, isBadge = false }) {
  return (
    <div className="info-block">
      <h3>{title}</h3>
      {items?.length ? (
        <div className={isBadge ? "badges" : "simple-list"}>
          {items.map((item) => (
            <span key={item}>{item}</span>
          ))}
        </div>
      ) : (
        <p className="muted">{empty}</p>
      )}
    </div>
  );
}
