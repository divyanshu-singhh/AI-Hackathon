import { Images, Play } from "lucide-react";
import { useState } from "react";
import { processMultipleImages } from "../api/client.js";
import Loader from "./Loader.jsx";

export default function BatchUploadPanel({ stages, onBatch }) {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    if (!files.length) return;
    setLoading(true);
    setError("");
    try {
      onBatch(await processMultipleImages(files, stages));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel">
      <div className="section-heading">
        <Images size={18} />
        <h2>Multi Image</h2>
      </div>
      <label className="file-picker">
        <input type="file" multiple accept="image/png,image/jpeg,image/webp" onChange={(event) => setFiles(Array.from(event.target.files || []))} />
        Select Images
      </label>
      {files.length ? (
        <div className="file-list">
          {files.map((file) => <span key={file.name}>{file.name}</span>)}
        </div>
      ) : null}
      <button className="primary-button" type="button" disabled={!files.length || loading} onClick={submit}>
        <Play size={18} />
        Process All
      </button>
      {loading ? <Loader label={`Processing ${files.length} image${files.length === 1 ? "" : "s"}`} /> : null}
      {error ? <p className="error-line">{error}</p> : null}
    </section>
  );
}
