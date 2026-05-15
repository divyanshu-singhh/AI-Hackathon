import { useState } from "react";
import Header from "./components/Header.jsx";
import UploadPanel from "./components/UploadPanel.jsx";
import BatchUploadPanel from "./components/BatchUploadPanel.jsx";
import GoogleSheetPanel from "./components/GoogleSheetPanel.jsx";
import ResultsTable from "./components/ResultsTable.jsx";
import StageSelector from "./components/StageSelector.jsx";
import ProgressTimeline from "./components/ProgressTimeline.jsx";
import CropSelector from "./components/CropSelector.jsx";
import BatchPreviewGrid from "./components/BatchPreviewGrid.jsx";
import { PanelLeftClose, PanelLeftOpen } from "lucide-react";

const DEFAULT_STAGES = new Set(["quality", "background", "rebuild"]);

export default function App() {
  const [tab, setTab] = useState("single");
  const [stages, setStages] = useState(DEFAULT_STAGES);
  const [batchResult, setBatchResult] = useState(null);
  const [progressEvents, setProgressEvents] = useState([]);
  const [progressState, setProgressState] = useState("idle");
  const [cropSize, setCropSize] = useState(500);
  const [controlsCollapsed, setControlsCollapsed] = useState(false);

  function handleBatch(result) {
    setBatchResult(result);
    setControlsCollapsed(true);
  }

  function handleSingle(result) {
    setBatchResult({
      batch_id: result.image_id,
      total: 1,
      success: result.status === "success" ? 1 : 0,
      failed: result.status === "success" ? 0 : 1,
      results: [result]
    });
    setControlsCollapsed(true);
  }

  function resetProgress() {
    setProgressEvents([]);
    setProgressState("connecting");
  }

  function addProgressEvent(event) {
    setProgressEvents((current) => [...current, event]);
  }

  return (
    <main>
      <Header />
      <section className={controlsCollapsed ? "workspace controls-collapsed" : "workspace"}>
        <aside className="control-column">
          <button className="collapse-button" type="button" onClick={() => setControlsCollapsed((value) => !value)}>
            {controlsCollapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
            <span>{controlsCollapsed ? "Expand Inputs" : "Collapse Inputs"}</span>
          </button>
          {controlsCollapsed ? null : (
            <>
          <nav className="tabs" aria-label="Upload modes">
            <button className={tab === "single" ? "active" : ""} onClick={() => setTab("single")}>Single</button>
            <button className={tab === "multi" ? "active" : ""} onClick={() => setTab("multi")}>Multi</button>
            <button className={tab === "csv" ? "active" : ""} onClick={() => setTab("csv")}>CSV</button>
          </nav>
          <StageSelector selected={stages} onChange={setStages} />
          <CropSelector value={cropSize} onChange={setCropSize} />
          {tab === "single" ? (
            <UploadPanel stages={stages} cropSize={cropSize} onResult={handleSingle} onProgressReset={resetProgress} onProgressEvent={addProgressEvent} onProgressState={setProgressState} />
          ) : null}
          {tab === "multi" ? (
            <BatchUploadPanel stages={stages} cropSize={cropSize} onBatch={handleBatch} onProgressReset={resetProgress} onProgressEvent={addProgressEvent} onProgressState={setProgressState} />
          ) : null}
          {tab === "csv" ? (
            <GoogleSheetPanel stages={stages} cropSize={cropSize} onBatch={handleBatch} onProgressReset={resetProgress} onProgressEvent={addProgressEvent} onProgressState={setProgressState} />
          ) : null}
            </>
          )}
        </aside>
        <section className="result-column">
          <ProgressTimeline events={progressEvents} connectionState={progressState} />
          <BatchPreviewGrid results={batchResult?.results || []} />
          <ResultsTable batch={batchResult} />
        </section>
      </section>
    </main>
  );
}
