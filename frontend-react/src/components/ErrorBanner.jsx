export default function ErrorBanner({ error }) {
  if (!error) return null;

  return (
    <section className="error-banner" role="alert" aria-live="polite">
      <p className="error-title">{error.message || "Unexpected error"}</p>
      {Array.isArray(error.details) && error.details.length > 0 ? (
        <ul className="error-details">
          {error.details.map((d, idx) => (
            <li key={`${d.field || "field"}-${idx}`}>
              <code>{d.field || "unknown"}</code>: {d.issue || "Invalid value"}
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
