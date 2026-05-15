const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const WS_BASE_URL = API_BASE_URL.replace(/^http/, "ws");

export function createJobId() {
  if (globalThis.crypto?.randomUUID) {
    return globalThis.crypto.randomUUID();
  }
  return `job-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function subscribeToProgress(jobId, onEvent, onStateChange) {
  const socket = new WebSocket(`${WS_BASE_URL}/ws/progress/${jobId}`);
  socket.addEventListener("open", () => onStateChange?.("connected"));
  socket.addEventListener("message", (event) => {
    try {
      onEvent(JSON.parse(event.data));
    } catch {
      onStateChange?.("invalid-message");
    }
  });
  socket.addEventListener("close", () => onStateChange?.("closed"));
  socket.addEventListener("error", () => onStateChange?.("error"));
  return () => socket.close();
}

function stageString(stages) {
  return Array.from(stages || []).join(",");
}

async function readJson(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || data.error || "Request failed");
  }
  return data;
}

export async function processSingleImage(file, stages, jobId, cropSize) {
  const formData = new FormData();
  formData.append("image", file);
  formData.append("stages", stageString(stages));
  if (jobId) formData.append("job_id", jobId);
  if (cropSize) formData.append("crop_size", cropSize);
  const response = await fetch(`${API_BASE_URL}/api/process-image`, {
    method: "POST",
    body: formData
  });
  return readJson(response);
}

export async function processMultipleImages(files, stages, jobId, cropSize) {
  const formData = new FormData();
  Array.from(files).forEach((file) => formData.append("images", file));
  formData.append("stages", stageString(stages));
  if (jobId) formData.append("job_id", jobId);
  if (cropSize) formData.append("crop_size", cropSize);
  const response = await fetch(`${API_BASE_URL}/api/process-images`, {
    method: "POST",
    body: formData
  });
  return readJson(response);
}

export async function processCsv(file, stages, jobId, cropSize) {
  const formData = new FormData();
  formData.append("csv_file", file);
  formData.append("stages", stageString(stages));
  if (jobId) formData.append("job_id", jobId);
  if (cropSize) formData.append("crop_size", cropSize);
  const response = await fetch(`${API_BASE_URL}/api/process-csv`, {
    method: "POST",
    body: formData
  });
  return readJson(response);
}

export async function processSheetUrl(csvUrl, stages, jobId, cropSize) {
  const response = await fetch(`${API_BASE_URL}/api/process-sheet-url`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ csv_url: csvUrl, stages: Array.from(stages || []), job_id: jobId, crop_size: cropSize })
  });
  return readJson(response);
}

export function reportDownloadUrl(reportName) {
  return `${API_BASE_URL}/api/reports/${reportName}`;
}
