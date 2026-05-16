import { useState } from "react";
import Header from "./components/Header.jsx";
import BatchUploadPanel from "./components/BatchUploadPanel.jsx";
import GoogleSheetPanel from "./components/GoogleSheetPanel.jsx";
import ResultsTable from "./components/ResultsTable.jsx";
import StageSelector from "./components/StageSelector.jsx";
import ProgressTimeline from "./components/ProgressTimeline.jsx";
import CropSelector from "./components/CropSelector.jsx";
import BatchPreviewGrid from "./components/BatchPreviewGrid.jsx";
import Loader from "./components/Loader.jsx";
import { PanelLeftClose, PanelLeftOpen } from "lucide-react";

const DEFAULT_STAGES = new Set(["quality", "background", "rebuild"]);

export default function App() {
  const [tab, setTab] = useState("image");
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
            <button className={tab === "image" ? "active" : ""} onClick={() => setTab("image")}>Image</button>
            <button className={tab === "csv" ? "active" : ""} onClick={() => setTab("csv")}>CSV</button>
          </nav>
          <StageSelector selected={stages} onChange={setStages} />
          <CropSelector value={cropSize} onChange={setCropSize} />
          {tab === "image" ? (
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
          {batchResult?.total_estimated_cost_display ? (
            <Loader label="Final LLM cost" cost={batchResult.total_estimated_cost_display} done />
          ) : null}
          <BatchPreviewGrid results={batchResult?.results || []} />
          <ResultsTable batch={batchResult} />
        </section>
      </section>
    </main>
  );
}
