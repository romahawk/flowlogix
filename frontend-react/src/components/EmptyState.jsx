export default function EmptyState() {
  return (
    <section className="empty-state" aria-live="polite">
      <h2>No orders match this filter set</h2>
      <p>Adjust one or more filters to broaden results.</p>
    </section>
  );
}
