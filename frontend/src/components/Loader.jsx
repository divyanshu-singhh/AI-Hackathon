export default function Loader({ label = "Processing", cost = "", done = false }) {
  return (
    <div className="loader" role="status" aria-live="polite">
      {done ? null : <span />}
      {label}
      {cost ? <strong>{cost}</strong> : null}
    </div>
  );
}
