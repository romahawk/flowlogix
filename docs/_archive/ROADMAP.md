# FlowLogix – Roadmap

This roadmap outlines the evolution of the FlowLogix Supply Tracker from an internal tool to a wider logistics dashboard or micro-SaaS product.

---

## 🚀 Short-Term (Next 1–2 Months)

**1. Role-Based Access (RBAC)**
- Add Admin, Company User, and Read-Only user types
- Restrict views and actions based on user/company
- Improve session handling and security

**2. Stockreport Module Enhancements**
- Finalize the Stockreport modal (Arrived / Stocked / Delivered)
- Add CRUD logic for all tabs
- Validate quantities and cargo transitions
- Add minimal activity log for reporting

**3. UX Consistency + Minor Refactors**
- Unify table actions across Dashboard, Warehouse, Delivered
- Improve mobile responsiveness
- Polish dark mode (especially modal backgrounds)
- Add inline validation for ETD/ETA/ATA

---

## 📊 Medium-Term (2–6 Months)

**4. Analytics & Insights**
- Lead time analytics (order → arrival → delivery)
- Bottleneck analysis per supplier / shipper
- On-time delivery KPI dashboard
- Export to Excel/CSV for reporting

**5. API Layer + Integrations**
- Expose REST API endpoints for:
  - creating/updating orders
  - fetching filtered lists
  - analytics summaries
- Optional integration with ERP/WMS systems

**6. React Frontend (Optional Parallel Track)**
- New `frontend-react/` directory
- Build modern UI consuming Flask API
- Reuse current Flask HTML version as a “classic UI”

---

## 🌐 Long-Term (6–18 Months)

**7. Multi-Tenant Architecture**
- Allow multiple companies to use the system with isolated workspaces
- Admin dashboard for tenant management
- Custom branding per customer

**8. SaaS Evolution – FlowLogix**
- Subscription tiers (Starter / Pro / Enterprise)
- API rate limits
- Automated invoicing
- Email/SMS notifications for delays

**9. Infrastructure Improvements**
- Migrate to PostgreSQL for production
- Add CI/CD pipeline
- Automated backups & monitoring
- Containerization (Docker)

---

## 🧭 Positioning & Strategic Vision

FlowLogix is growing from:

**Internal logistics dashboard → lightweight SME tool → micro-SaaS platform.**

Core value:
- fast overview of shipments,
- predictable deadlines,
- transparency for warehouse & operations teams.

---

## ✔ Status: Actively Developed

This roadmap evolves based on real usage from pharmaceutical logistics company and new project opportunities.
<<<<<<< HEAD
=======

>>>>>>> 984c2f7d744f643c8ad9ecca702b4c040353cc5d
