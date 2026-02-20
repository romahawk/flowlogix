import { Pencil, Plane, Ship, Trash2, Truck, Warehouse as WarehouseIcon } from "lucide-react";

function safe(value) {
  return value || "-";
}

function formatQuantity(value) {
  const parsed = Number.parseFloat(String(value ?? ""));
  return Number.isFinite(parsed) ? parsed.toFixed(2) : "-";
}

function formatDate(value) {
  if (!value) return "-";
  const parts = String(value).split("-");
  if (parts.length !== 3) return value;
  return `${parts[2]}.${parts[1]}.${parts[0].slice(-2)}`;
}

function transportIcon(value) {
  const raw = String(value || "").toLowerCase();
  if (raw.includes("air")) return <Plane size={14} />;
  if (raw.includes("sea")) return <Ship size={14} />;
  if (raw.includes("truck")) return <Truck size={14} />;
  return <Truck size={14} />;
}

function isArrived(status) {
  return String(status || "").toLowerCase().replaceAll("_", " ").includes("arrived");
}

export default function OrdersTable({
  rows,
  role,
  busyId,
  onMoveWarehouse,
  onDeliverDirect,
  highlightedId,
  pinnedId,
  onRowHover,
  onRowLeave,
  onRowPin,
}) {
  const roleName = String(role || "").toLowerCase();
  const canMutate = roleName !== "superuser" && roleName !== "viewer";

  return (
    <div className="orders-table-wrap">
      <table className="orders-table">
        <thead>
          <tr>
            <th>Order Date</th>
            <th>Order #</th>
            <th>Product Name</th>
            <th>Buyer</th>
            <th>Responsible</th>
            <th>Quantity</th>
            <th>Required Delivery</th>
            <th>Terms</th>
            <th>Payment Date</th>
            <th>ETD</th>
            <th>ETA</th>
            <th>ATA</th>
            <th>Transit Status</th>
            <th>Transport</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((order) => {
            const moveAllowed = canMutate && isArrived(order.transit_status);
            const rowBusy = busyId === order.id;
            const isHighlighted = highlightedId === order.id;
            const isPinned = pinnedId === order.id;

            return (
              <tr
                key={order.id}
                className={isHighlighted ? "synced-highlight" : ""}
                tabIndex={0}
                aria-selected={isPinned}
                onMouseEnter={() => onRowHover?.(order.id)}
                onMouseLeave={() => onRowLeave?.()}
                onFocus={() => onRowHover?.(order.id)}
                onBlur={() => onRowLeave?.()}
                onClick={() => onRowPin?.(order.id)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    onRowPin?.(order.id);
                  }
                }}
              >
                <td>{formatDate(order.order_date)}</td>
                <td>{safe(order.order_number)}</td>
                <td>{safe(order.product_name)}</td>
                <td>{safe(order.buyer)}</td>
                <td>{safe(order.responsible)}</td>
                <td>{formatQuantity(order.quantity)}</td>
                <td>{safe(order.required_delivery)}</td>
                <td>{safe(order.terms_of_delivery)}</td>
                <td>{formatDate(order.payment_date)}</td>
                <td>{formatDate(order.etd)}</td>
                <td>{formatDate(order.eta)}</td>
                <td>{formatDate(order.ata)}</td>
                <td>{safe(order.transit_status)}</td>
                <td>
                  <span className="transport-cell" title={safe(order.transport)}>
                    {transportIcon(order.transport)}
                  </span>
                </td>
                <td>
                  <div className="action-cell">
                    <button
                      type="button"
                      className="icon-btn"
                      disabled
                      title="Edit (Sprint 4)"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <Pencil size={13} />
                    </button>
                    <button
                      type="button"
                      className="icon-btn danger"
                      disabled
                      title="Delete (Sprint 4)"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <Trash2 size={13} />
                    </button>
                    <button
                      type="button"
                      className="icon-btn move"
                      disabled={!moveAllowed || rowBusy}
                      onClick={(e) => {
                        e.stopPropagation();
                        onMoveWarehouse(order.id);
                      }}
                      title="Move to Warehouse"
                    >
                      <WarehouseIcon size={13} />
                    </button>
                    <button
                      type="button"
                      className="icon-btn deliver"
                      disabled={!moveAllowed || rowBusy}
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeliverDirect(order.id);
                      }}
                      title="Mark Delivered"
                    >
                      <Truck size={13} />
                    </button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
