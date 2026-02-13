export default function Pagination({ page, perPage, total, onPageChange }) {
  const currentPage = Number(page);
  const size = Number(perPage);
  const totalCount = Number(total || 0);
  const totalPages = Math.max(1, Math.ceil(totalCount / size));

  return (
    <nav className="pagination" aria-label="Orders pagination">
      <button onClick={() => onPageChange(String(Math.max(1, currentPage - 1)))} disabled={currentPage <= 1}>
        Previous
      </button>
      <span>
        Page {currentPage} / {totalPages} ({totalCount} total)
      </span>
      <button
        onClick={() => onPageChange(String(Math.min(totalPages, currentPage + 1)))}
        disabled={currentPage >= totalPages}
      >
        Next
      </button>
    </nav>
  );
}
