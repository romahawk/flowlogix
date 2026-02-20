export default function LoadingSkeleton() {
  return (
    <section className="skeleton" aria-live="polite" aria-label="Loading orders">
      <div className="skeleton-bar" />
      <div className="skeleton-row" />
      <div className="skeleton-row" />
      <div className="skeleton-row" />
      <div className="skeleton-row" />
    </section>
  );
}
