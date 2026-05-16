import { Images, Play } from "lucide-react";
import { useState } from "react";
import { createJobId, processMultipleImages, subscribeToProgress } from "../api/client.js";
import Loader from "./Loader.jsx";

export default function BatchUploadPanel({ stages, cropSize, onBatch, onProgressReset, onProgressEvent, onProgressState }) {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    if (!files.length) return;
    setLoading(true);
    setError("");
    const jobId = createJobId();
    onProgressReset?.(jobId);
    const closeProgress = subscribeToProgress(jobId, onProgressEvent, onProgressState);
    try {
      onBatch(await processMultipleImages(files, stages, jobId, cropSize));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setTimeout(closeProgress, 1200);
    }
  }

  return (
    <section className="panel">
      <div className="section-heading">
        <Images size={18} />
        <h2>Image</h2>
      </div>
      <label className="file-picker">
        <input type="file" multiple accept="image/png,image/jpeg,image/webp" onChange={(event) => setFiles(Array.from(event.target.files || []))} />
        Select Image
      </label>
      {files.length ? (
        <div className="file-list">
          {files.map((file) => <span key={file.name}>{file.name}</span>)}
        </div>
      ) : null}
      <button className="primary-button" type="button" disabled={!files.length || loading} onClick={submit}>
        <Play size={18} />
        Process Image
      </button>
      {loading ? <Loader label={`Processing ${files.length} image${files.length === 1 ? "" : "s"}`} /> : null}
      {error ? <p className="error-line">{error}</p> : null}
    </section>
  );
}
