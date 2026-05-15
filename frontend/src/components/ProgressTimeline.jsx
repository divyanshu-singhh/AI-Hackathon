import { Activity } from "lucide-react";

const STATUS_LABELS = {
  running: "Running",
  completed: "Done",
  skipped: "Skipped",
  failed: "Failed"
};

export default function ProgressTimeline({ events, connectionState }) {
  const latestByStage = collapseEvents(events);
  const rows = Object.values(latestByStage);
  const current = [...rows].reverse().find((row) => row.status === "running");
  const overallPercent = rows.length ? Math.max(...rows.map((row) => row.percent || 0)) : 0;

  return (
    <section className="timeline-section">
      <div className="table-header">
        <div>
          <div className="section-heading timeline-heading">
            <Activity size={18} />
            <h2>Processing Timeline</h2>
          </div>
          <p className="muted">
            {current ? `Current stage: ${current.stage}` : rows.length ? "Pipeline updated" : "No job started yet"}
          </p>
        </div>
        <div className="progress-summary">
          <strong>{overallPercent}%</strong>
          <span>{connectionState || "idle"}</span>
        </div>
      </div>
      <div className="progress-bar" aria-label="Overall progress">
        <span style={{ width: `${overallPercent}%` }} />
      </div>
      <div className="table-wrap">
        <table className="timeline-table">
          <thead>
            <tr>
              <th>Stage</th>
              <th>Status</th>
              <th>Done</th>
              <th>Model / Tool</th>
              <th>Type</th>
              <th>Tokens</th>
              <th>Cost</th>
              <th>Message</th>
            </tr>
          </thead>
          <tbody>
            {rows.length ? (
              rows.map((row) => (
                <tr key={row.stage_id}>
                  <td>{row.stage}</td>
                  <td><span className={`pill ${row.status}`}>{STATUS_LABELS[row.status] || row.status}</span></td>
                  <td>{row.percent}%</td>
                  <td>{row.model_name || "-"}</td>
                  <td>{row.model_type || "-"}</td>
                  <td>{formatTokens(row)}</td>
                  <td>{row.estimated_cost || "-"}</td>
                  <td>{row.message || "-"}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="8" className="muted">Start processing to see live stage updates.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function collapseEvents(events) {
  return events.reduce((acc, event) => {
    acc[event.stage_id] = event;
    return acc;
  }, {});
}

function formatTokens(row) {
  if (!row.tokens_used) {
    return "-";
  }
  return `${row.tokens_used} (${row.prompt_tokens || 0}+${row.completion_tokens || 0})`;
}
