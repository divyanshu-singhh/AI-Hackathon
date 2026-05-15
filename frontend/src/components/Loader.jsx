export default function Loader({ label = "Processing" }) {
  return (
    <div className="loader" role="status" aria-live="polite">
      <span />
      {label}
    </div>
  );
}
