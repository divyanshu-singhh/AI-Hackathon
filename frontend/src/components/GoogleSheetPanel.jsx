import { FileSpreadsheet, Link, Play } from "lucide-react";
import { useState } from "react";
import { processCsv, processSheetUrl } from "../api/client.js";
import Loader from "./Loader.jsx";

export default function GoogleSheetPanel({ stages, onBatch }) {
  const [csvFile, setCsvFile] = useState(null);
  const [csvUrl, setCsvUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submitCsv() {
    if (!csvFile) return;
    setLoading(true);
    setError("");
    try {
      onBatch(await processCsv(csvFile, stages));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function submitUrl() {
    if (!csvUrl.trim()) return;
    setLoading(true);
    setError("");
    try {
      onBatch(await processSheetUrl(csvUrl.trim(), stages));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel">
      <div className="section-heading">
        <FileSpreadsheet size={18} />
        <h2>CSV / Sheet</h2>
      </div>
      <label className="file-picker">
        <input type="file" accept=".csv,text/csv" onChange={(event) => setCsvFile(event.target.files?.[0] || null)} />
        {csvFile ? csvFile.name : "Select CSV"}
      </label>
      <button className="primary-button" type="button" disabled={!csvFile || loading} onClick={submitCsv}>
        <Play size={18} />
        Process CSV
      </button>
      <div className="url-row">
        <Link size={18} />
        <input value={csvUrl} placeholder="Google Sheet CSV export URL" onChange={(event) => setCsvUrl(event.target.value)} />
      </div>
      <button className="secondary-button" type="button" disabled={!csvUrl.trim() || loading} onClick={submitUrl}>
        Process URL
      </button>
      {loading ? <Loader label="Processing batch" /> : null}
      {error ? <p className="error-line">{error}</p> : null}
    </section>
  );
}
