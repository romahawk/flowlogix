# Sprint 3 – Stockreport & UX Refinements
**Duration:** 1 week  
**Sprint Goal:** Introduce Stockreport (warehouse-level cargo tracking) and unify UX across all pages.

---

## 🎯 Objectives
- Build Stockreport modal with Arrived / Stocked / Delivered sections
- Improve visual consistency across Dashboard, Warehouse, Delivered
- Strengthen validation logic for ETD/ETA/ATA
- Polish dark mode, navbar, forms, and modal interactions

---

## ✅ Completed Work
- Initial Stockreport functionality implemented (view + edit)
- `view_stockreport.html` modal created with multi-tab layout
- Validation added to prevent invalid ETD/ETA/ATA combinations
- Dark mode styling aligned across all pages
- Navbar/Sidebar standardized across templates
- Improved layout responsiveness (mobile-friendly)

---

## ❗ Not Completed / Deferred
- Full Stockreport CRUD (for all statuses)
- User-based restrictions for editing Stockreport entries
- Advanced analytics (lead time, delays)

---

## 🔎 Demo Summary
Users can now:
- Open a Stockreport modal and view breakdown by Arrived/Stocked/Delivered  
- Edit basic warehouse-related fields  
- Experience a more consistent and polished UI/UX  

---

## 🔄 Retrospective
**What went well**
- Modal-based editing significantly improved usability  
- Validation enhancements reduced common data-entry errors  

**What to improve**
- Stockreport backend logic still needs a more robust foundation  
- Need to introduce role-specific editing permissions
