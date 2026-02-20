import { Circle, Plane, Ship, Truck } from "lucide-react";

function parseIsoDate(value) {
  if (!value) return null;
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? null : d;
}

function clamp(date, min, max) {
  if (date < min) return min;
  if (date > max) return max;
  return date;
}

function startOfYear(year) {
  return new Date(year, 0, 1);
}

function endOfYear(year) {
  return new Date(year, 11, 31);
}

function transportIcon(value) {
  const raw = String(value || "").toLowerCase();
  if (raw.includes("air")) return <Plane size={13} />;
  if (raw.includes("sea")) return <Ship size={13} />;
  if (raw.includes("truck")) return <Truck size={13} />;
  return <Truck size={13} />;
}

function statusClass(status) {
  const s = String(status || "").toLowerCase().replaceAll("_", " ");
  if (s.includes("arrived")) return "arrived";
  if (s.includes("en route")) return "enroute";
  return "inprocess";
}

function collectYears(rows) {
  const set = new Set();
  for (const row of rows) {
    for (const fld of ["order_date", "etd", "eta", "ata"]) {
      const d = parseIsoDate(row[fld]);
      if (d) set.add(d.getFullYear());
    }
  }
  return Array.from(set).sort((a, b) => b - a);
}

export default function TimelineGantt({
  rows,
  year,
  onYearChange,
  highlightedId,
  pinnedId,
  onItemHover,
  onItemLeave,
  onItemPin,
}) {
  const weeks = Array.from({ length: 52 }, (_, i) => i + 1);
  const years = collectYears(rows);
  const effectiveYear = Number(year) || years[0] || new Date().getFullYear();
  const yearStart = startOfYear(effectiveYear);
  const yearEnd = endOfYear(effectiveYear);
  const totalMs = yearEnd.getTime() - yearStart.getTime();

  const bars = rows
    .map((row) => {
      const rawStart = parseIsoDate(row.etd) || parseIsoDate(row.order_date);
      const rawEnd = parseIsoDate(row.ata) || parseIsoDate(row.eta);
      if (!rawStart || !rawEnd) return null;

      const endExtended = new Date(rawEnd);
      endExtended.setDate(endExtended.getDate() + 7);

      if (endExtended < yearStart || rawStart > yearEnd) return null;

      const clippedStart = clamp(rawStart, yearStart, yearEnd);
      const clippedEnd = clamp(endExtended, yearStart, yearEnd);

      const left = ((clippedStart.getTime() - yearStart.getTime()) / totalMs) * 100;
      const width = Math.max(0.7, ((clippedEnd.getTime() - clippedStart.getTime()) / totalMs) * 100);

      return {
        id: row.id,
        productName: row.product_name,
        orderNumber: row.order_number,
        transport: row.transport,
        transitStatus: row.transit_status,
        left,
        width,
        statusClass: statusClass(row.transit_status),
      };
    })
    .filter(Boolean);

  return (
    <section className="timeline-section">
      <div className="timeline-head">
        <h2>Timeline</h2>
      </div>

      <div className="timeline-controls">
        <label className="timeline-year">
          Select Year
          <select value={String(effectiveYear)} onChange={(e) => onYearChange(e.target.value)}>
            {[...new Set([effectiveYear, ...years])].sort((a, b) => b - a).map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </label>

        <div className="timeline-legend" role="list" aria-label="Timeline status legend">
          <span role="listitem"><Circle size={12} className="dot inprocess" />In Process</span>
          <span role="listitem"><Circle size={12} className="dot enroute" />En Route</span>
          <span role="listitem"><Circle size={12} className="dot arrived" />Arrived</span>
        </div>

        <div aria-hidden="true" />
      </div>

      {bars.length === 0 ? (
        <p className="timeline-empty">No timeline rows for selected year/page state.</p>
      ) : (
        <div className="timeline-grid">
          <div className="timeline-weeks">
            <div className="timeline-weeks-label" aria-hidden="true" />
            <div className="timeline-weeks-track">
              {weeks.map((week) => (
                <span key={week}>W{week}</span>
              ))}
            </div>
          </div>

          <div className="timeline-body">
            {bars.map((bar) => (
              <div
                className={`timeline-row ${highlightedId === bar.id ? "synced-highlight" : ""}`}
                key={bar.id}
                tabIndex={0}
                aria-selected={pinnedId === bar.id}
                onMouseEnter={() => onItemHover?.(bar.id)}
                onMouseLeave={() => onItemLeave?.()}
                onFocus={() => onItemHover?.(bar.id)}
                onBlur={() => onItemLeave?.()}
                onClick={() => onItemPin?.(bar.id)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    onItemPin?.(bar.id);
                  }
                }}
              >
                <div className="timeline-label">
                  {transportIcon(bar.transport)}
                  <span>{bar.productName} ({bar.orderNumber})</span>
                </div>
                <div className="timeline-lane">
                  <div
                    className={`timeline-bar ${bar.statusClass}`}
                    style={{ left: `${bar.left}%`, width: `${bar.width}%` }}
                    title={`${bar.productName} (${bar.orderNumber}) - ${bar.transitStatus || "in process"}`}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
