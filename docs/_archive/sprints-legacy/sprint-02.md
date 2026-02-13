# Sprint 2 – Warehouse & Delivered Views
**Duration:** 1 week  
**Sprint Goal:** Support the entire shipment lifecycle by adding Warehouse and Delivered sections.

---

## 🎯 Objectives
- Add Warehouse view for arrived cargo
- Add Delivered view for completed shipments
- Enable transitions:
  - In Process → Warehouse
  - Warehouse → Delivered
- Ensure consistent table layout across all tabs

---

## ✅ Completed Work
- `warehouse_routes.py` and `delivered_routes.py` created
- `warehouse.html` and `delivered.html` implemented
- Status update logic added in backend
- Filters (year, buyer, responsible, transit status) added to new tabs
- Table sorting unified with dashboard
- Demo dataset expanded to cover all states

---

## ❗ Not Completed / Deferred
- Stockreport domain model
- Stock-level events inside warehouse
- Company-level access restrictions

---

## 🔎 Demo Summary
Users can now:
- Switch between Dashboard → Warehouse → Delivered  
- Update shipment status through each lifecycle stage  
- Use filters and sorting consistently across pages  

---

## 🔄 Retrospective
**What went well**
- Lifecycle separation greatly improved clarity for end users  
- Code structure in routes allowed easier maintenance  

**What to improve**
- Need to standardize modals/actions across all pages  
- Begin planning Stockreport domain early to avoid later refactor
