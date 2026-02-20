const SORT_OPTIONS = [
  { value: "eta:desc,etd:desc,order_date:desc,id:desc", label: "ETA desc (default)" },
  { value: "eta:asc,etd:asc,order_date:asc,id:desc", label: "ETA asc" },
  { value: "order_date:desc,id:desc", label: "Order date desc" },
  { value: "order_date:asc,id:desc", label: "Order date asc" },
];

const PER_PAGE_OPTIONS = ["10", "25", "50", "100"];

export default function OrdersToolbar({ query, onPatch, onReset }) {
  return (
    <section className="orders-toolbar" aria-label="Orders filters and sorting">
      <div className="search-row">
        <input
          type="search"
          className="search-input"
          value={query["filter[q]"]}
          placeholder="Search orders (product, order #, status)"
          aria-label="Search orders"
          onChange={(e) => onPatch({ "filter[q]": e.target.value })}
        />
      </div>

      <div className="field-grid">
        <label>
          Transit status
          <input
            aria-label="Filter by transit status"
            value={query["filter[transit_status]"]}
            placeholder="in process / en route / arrived"
            onChange={(e) => onPatch({ "filter[transit_status]": e.target.value })}
          />
        </label>

        <label>
          Buyer
          <input
            aria-label="Filter by buyer"
            value={query["filter[buyer]"]}
            onChange={(e) => onPatch({ "filter[buyer]": e.target.value })}
          />
        </label>

        <label>
          Responsible
          <input
            aria-label="Filter by responsible person"
            value={query["filter[responsible]"]}
            onChange={(e) => onPatch({ "filter[responsible]": e.target.value })}
          />
        </label>

        <label>
          Year
          <input
            type="number"
            inputMode="numeric"
            min="1990"
            max="2100"
            aria-label="Filter by year"
            value={query["filter[year]"]}
            placeholder="2025"
            onChange={(e) => onPatch({ "filter[year]": e.target.value })}
          />
        </label>

        <label>
          Transport
          <input
            aria-label="Filter by transport"
            value={query["filter[transport]"]}
            placeholder="air / sea / truck"
            onChange={(e) => onPatch({ "filter[transport]": e.target.value })}
          />
        </label>

        <label>
          Sort
          <select
            aria-label="Sort orders"
            value={query.sort}
            onChange={(e) => onPatch({ sort: e.target.value })}
          >
            {SORT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="toolbar-row">
        <label>
          Per page
          <select
            aria-label="Rows per page"
            value={query.per_page}
            onChange={(e) => onPatch({ per_page: e.target.value })}
          >
            {PER_PAGE_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
        <button type="button" className="reset-btn" onClick={onReset}>
          Reset filters
        </button>
      </div>
    </section>
  );
}
