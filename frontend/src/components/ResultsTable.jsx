import { Download } from "lucide-react";
import { reportDownloadUrl } from "../api/client.js";

export default function ResultsTable({ batch }) {
  const results = batch?.results || [];
  if (!results.length) {
    return null;
  }

  return (
    <section className="table-section">
      <div className="table-header">
        <div>
          <h2>Batch Results</h2>
          <p className="muted">
            {batch.success || 0} success / {batch.failed || 0} failed / {batch.total || results.length} total
          </p>
        </div>
        {batch.report_name ? (
          <a className="primary-button compact" href={reportDownloadUrl(batch.report_name)}>
            <Download size={16} />
            CSV
          </a>
        ) : null}
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Image</th>
              <th>Status</th>
              <th>Category</th>
              <th>Quality</th>
              <th>Objects</th>
              <th>Tags</th>
              <th>Issues</th>
              <th>Output</th>
            </tr>
          </thead>
          <tbody>
            {results.map((row) => (
              <tr key={row.image_id}>
                <td>{row.file_name}</td>
                <td><span className={`pill ${row.status}`}>{row.status}</span></td>
                <td>{row.category || "-"}</td>
                <td>{row.quality_score ?? "-"}</td>
                <td>{(row.detected_objects || []).join(", ") || "-"}</td>
                <td>{(row.tags || []).join(", ") || "-"}</td>
                <td>{(row.issues || []).slice(0, 2).join("; ") || "-"}</td>
                <td>
                  {row.rebuilt_image_url ? <a href={row.rebuilt_image_url} target="_blank">View</a> : "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
