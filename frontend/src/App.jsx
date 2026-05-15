import { useState } from "react";
import Header from "./components/Header.jsx";
import UploadPanel from "./components/UploadPanel.jsx";
import BatchUploadPanel from "./components/BatchUploadPanel.jsx";
import GoogleSheetPanel from "./components/GoogleSheetPanel.jsx";
import ResultCard from "./components/ResultCard.jsx";
import ResultsTable from "./components/ResultsTable.jsx";
import StageSelector from "./components/StageSelector.jsx";
import ProgressTimeline from "./components/ProgressTimeline.jsx";

const DEFAULT_STAGES = new Set(["quality", "background", "rebuild"]);

export default function App() {
  const [tab, setTab] = useState("single");
  const [stages, setStages] = useState(DEFAULT_STAGES);
  const [singleResult, setSingleResult] = useState(null);
  const [batchResult, setBatchResult] = useState(null);
  const [progressEvents, setProgressEvents] = useState([]);
  const [progressState, setProgressState] = useState("idle");

  function handleBatch(result) {
    setBatchResult(result);
    setSingleResult(result?.results?.[0] || null);
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
      <section className="workspace">
        <aside className="control-column">
          <nav className="tabs" aria-label="Upload modes">
            <button className={tab === "single" ? "active" : ""} onClick={() => setTab("single")}>Single</button>
            <button className={tab === "multi" ? "active" : ""} onClick={() => setTab("multi")}>Multi</button>
            <button className={tab === "csv" ? "active" : ""} onClick={() => setTab("csv")}>CSV</button>
          </nav>
          <StageSelector selected={stages} onChange={setStages} />
          {tab === "single" ? (
            <UploadPanel stages={stages} onResult={setSingleResult} onProgressReset={resetProgress} onProgressEvent={addProgressEvent} onProgressState={setProgressState} />
          ) : null}
          {tab === "multi" ? (
            <BatchUploadPanel stages={stages} onBatch={handleBatch} onProgressReset={resetProgress} onProgressEvent={addProgressEvent} onProgressState={setProgressState} />
          ) : null}
          {tab === "csv" ? (
            <GoogleSheetPanel stages={stages} onBatch={handleBatch} onProgressReset={resetProgress} onProgressEvent={addProgressEvent} onProgressState={setProgressState} />
          ) : null}
        </aside>
        <section className="result-column">
          <ProgressTimeline events={progressEvents} connectionState={progressState} />
          <ResultCard result={singleResult} />
          <ResultsTable batch={batchResult} />
        </section>
      </section>
    </main>
  );
}
