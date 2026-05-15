import { Crop } from "lucide-react";

const CROP_SIZES = [125, 250, 500];

export default function CropSelector({ value, onChange }) {
  return (
    <section className="stage-selector">
      <div className="section-heading">
        <Crop size={18} />
        <h2>Output Crop</h2>
      </div>
      <div className="segmented">
        {CROP_SIZES.map((size) => (
          <button
            className={value === size ? "active" : ""}
            key={size}
            type="button"
            onClick={() => onChange(size)}
          >
            {size}x{size}
          </button>
        ))}
      </div>
    </section>
  );
}
