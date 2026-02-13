const SORT_OPTIONS = [
  { value: "eta:desc,etd:desc,order_date:desc,id:desc", label: "ETA desc (default)" },
  { value: "eta:asc,etd:asc,order_date:asc,id:desc", label: "ETA asc" },
  { value: "order_date:desc,id:desc", label: "Order date desc" },
  { value: "order_date:asc,id:desc", label: "Order date asc" },
];

const PER_PAGE_OPTIONS = ["10", "25", "50", "100"];

export default function OrdersToolbar({ query, onPatch }) {
  return (
    <section className="orders-toolbar" aria-label="Orders filters and sorting">
      <div className="field-grid">
        <label>
          Search
          <input
            type="search"
            value={query["filter[q]"]}
            placeholder="order/product/buyer"
            onChange={(e) => onPatch({ "filter[q]": e.target.value })}
          />
        </label>

        <label>
          Status
          <input
            value={query["filter[transit_status]"]}
            placeholder="in_process"
            onChange={(e) => onPatch({ "filter[transit_status]": e.target.value })}
          />
        </label>

        <label>
          Year
          <input
            inputMode="numeric"
            value={query["filter[year]"]}
            placeholder="2025"
            onChange={(e) => onPatch({ "filter[year]": e.target.value })}
          />
        </label>

        <label>
          Buyer
          <input
            value={query["filter[buyer]"]}
            onChange={(e) => onPatch({ "filter[buyer]": e.target.value })}
          />
        </label>

        <label>
          Responsible
          <input
            value={query["filter[responsible]"]}
            onChange={(e) => onPatch({ "filter[responsible]": e.target.value })}
          />
        </label>

        <label>
          Transport
          <input
            value={query["filter[transport]"]}
            onChange={(e) => onPatch({ "filter[transport]": e.target.value })}
          />
        </label>
      </div>

      <div className="toolbar-row">
        <label>
          Sort
          <select value={query.sort} onChange={(e) => onPatch({ sort: e.target.value })}>
            {SORT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          Per page
          <select value={query.per_page} onChange={(e) => onPatch({ per_page: e.target.value })}>
            {PER_PAGE_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
      </div>
    </section>
  );
}
