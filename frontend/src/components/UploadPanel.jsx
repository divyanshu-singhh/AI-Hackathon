import { ImageUp, Play } from "lucide-react";
import { useMemo, useState } from "react";
import { createJobId, processSingleImage, subscribeToProgress } from "../api/client.js";
import Loader from "./Loader.jsx";

export default function UploadPanel({ stages, onResult, onProgressReset, onProgressEvent, onProgressState }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const preview = useMemo(() => (file ? URL.createObjectURL(file) : ""), [file]);

  async function submit() {
    if (!file) return;
    setLoading(true);
    setError("");
    const jobId = createJobId();
    onProgressReset?.(jobId);
    const closeProgress = subscribeToProgress(jobId, onProgressEvent, onProgressState);
    try {
      onResult(await processSingleImage(file, stages, jobId));
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
        <ImageUp size={18} />
        <h2>Single Image</h2>
      </div>
      <label className="dropzone">
        <input type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => setFile(event.target.files?.[0] || null)} />
        {preview ? <img src={preview} alt="Selected preview" /> : <span>Choose product image</span>}
      </label>
      <button className="primary-button" type="button" disabled={!file || loading} onClick={submit}>
        <Play size={18} />
        Process Image
      </button>
      {loading ? <Loader /> : null}
      {error ? <p className="error-line">{error}</p> : null}
    </section>
  );
}
