import { CheckSquare, Sparkles } from "lucide-react";

const STAGES = [
  ["quality", "Quality"],
  ["background", "Remove BG"],
  ["rebuild", "Rebuild"],
  ["ocr", "OCR Text"],
  ["vision", "Vision"],
  ["metadata", "Metadata"]
];

export default function StageSelector({ selected, onChange }) {
  function toggle(stage) {
    const next = new Set(selected);
    if (next.has(stage)) {
      next.delete(stage);
    } else {
      next.add(stage);
    }
    if (next.size) {
      onChange(next);
    }
  }

  function selectAll() {
    onChange(new Set(STAGES.map(([key]) => key)));
  }

  return (
    <section className="stage-selector" aria-label="Processing stages">
      <div className="section-heading">
        <CheckSquare size={18} />
        <h2>Stages</h2>
        <button className="ghost-button" type="button" onClick={selectAll} title="Select all stages">
          <Sparkles size={16} />
        </button>
      </div>
      <div className="stage-grid">
        {STAGES.map(([stage, label]) => (
          <label key={stage} className={selected.has(stage) ? "stage active" : "stage"}>
            <input type="checkbox" checked={selected.has(stage)} onChange={() => toggle(stage)} />
            {label}
          </label>
        ))}
      </div>
    </section>
  );
}
