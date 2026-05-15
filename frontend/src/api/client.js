const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

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

export async function processSingleImage(file, stages) {
  const formData = new FormData();
  formData.append("image", file);
  formData.append("stages", stageString(stages));
  const response = await fetch(`${API_BASE_URL}/api/process-image`, {
    method: "POST",
    body: formData
  });
  return readJson(response);
}

export async function processMultipleImages(files, stages) {
  const formData = new FormData();
  Array.from(files).forEach((file) => formData.append("images", file));
  formData.append("stages", stageString(stages));
  const response = await fetch(`${API_BASE_URL}/api/process-images`, {
    method: "POST",
    body: formData
  });
  return readJson(response);
}

export async function processCsv(file, stages) {
  const formData = new FormData();
  formData.append("csv_file", file);
  formData.append("stages", stageString(stages));
  const response = await fetch(`${API_BASE_URL}/api/process-csv`, {
    method: "POST",
    body: formData
  });
  return readJson(response);
}

export async function processSheetUrl(csvUrl, stages) {
  const response = await fetch(`${API_BASE_URL}/api/process-sheet-url`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ csv_url: csvUrl, stages: Array.from(stages || []) })
  });
  return readJson(response);
}

export function reportDownloadUrl(reportName) {
  return `${API_BASE_URL}/api/reports/${reportName}`;
}
