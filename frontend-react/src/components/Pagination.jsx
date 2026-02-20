export default function Pagination({ page, perPage, total, onPageChange }) {
  const currentPage = Number(page);
  const size = Number(perPage);
  const totalCount = Number(total || 0);
  const totalPages = Math.max(1, Math.ceil(totalCount / size));

  return (
    <nav className="pagination" aria-label="Orders pagination">
      <button
        type="button"
        onClick={() => onPageChange("1")}
        disabled={currentPage <= 1}
        aria-label="Go to first page"
      >
        First
      </button>
      <button
        type="button"
        onClick={() => onPageChange(String(Math.max(1, currentPage - 1)))}
        disabled={currentPage <= 1}
        aria-label="Go to previous page"
      >
        Prev
      </button>
      <span aria-live="polite">
        Page {currentPage} / {totalPages} ({totalCount} rows)
      </span>
      <button
        type="button"
        onClick={() => onPageChange(String(Math.min(totalPages, currentPage + 1)))}
        disabled={currentPage >= totalPages}
        aria-label="Go to next page"
      >
        Next
      </button>
      <button
        type="button"
        onClick={() => onPageChange(String(totalPages))}
        disabled={currentPage >= totalPages}
        aria-label="Go to last page"
      >
        Last
      </button>
    </nav>
  );
}
