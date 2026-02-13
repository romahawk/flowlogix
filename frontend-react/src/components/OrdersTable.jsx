function cell(value) {
  return value || "-";
}

export default function OrdersTable({ rows }) {
  return (
    <div className="orders-table-wrap">
      <table className="orders-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Order #</th>
            <th>Product</th>
            <th>Buyer</th>
            <th>Responsible</th>
            <th>Qty</th>
            <th>Status</th>
            <th>Transport</th>
            <th>ETD</th>
            <th>ETA</th>
            <th>ATA</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((order) => (
            <tr key={order.id}>
              <td>{order.id}</td>
              <td>{cell(order.order_number)}</td>
              <td>{cell(order.product_name)}</td>
              <td>{cell(order.buyer)}</td>
              <td>{cell(order.responsible)}</td>
              <td>{cell(order.quantity)}</td>
              <td>{cell(order.transit_status)}</td>
              <td>{cell(order.transport)}</td>
              <td>{cell(order.etd)}</td>
              <td>{cell(order.eta)}</td>
              <td>{cell(order.ata)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
