/* ========= FlowLogix Dashboard (API-integrated) =========
   - Loads years from /api/years
   - Loads orders for selected year from /api/orders?year=YYYY
   - Preserves existing UI/UX (sorting, filters, timeline, TomSelect, etc.)
========================================================= */

let showOrderDate = true;
let showPaymentDate = true;
let allOrders = []; // holds orders for the currently selected year
let selectedYear = null; // selected year value (string or number)
let visibleStatuses = ["in process", "en route", "arrived"];
let chartInstance = null;
let sortDirection = { order_date: "desc" };
let lastSortKey = "order_date";
let lastSortDirection = "desc";
let currentTableData = [];
let currentPage = 1;
let pageSize = 10;
const PAGE_SIZE_FIXED = 10;

// Timeline pagination + sort state
let tlData = [];          // full sorted/filtered set for timeline
let tlPage = 1;
const TL_PAGE_SIZE = 10;
let tlSortKey = "etd";    // "etd" | "product_name"
let tlSortDir = "asc";

function ensureTimelineWeekHeader() {
  const track = document.getElementById("timeline-week-track");
  if (!track || track.childElementCount > 0) return;
  for (let week = 1; week <= 52; week += 1) {
    const label = document.createElement("span");
    label.textContent = `W${week}`;
    track.appendChild(label);
  }
}

function syncTimelineWeekHeader(chart) {
  const header = document.getElementById("timeline-week-header");
  const track = document.getElementById("timeline-week-track");
  if (!header || !track) return;
  if (!chart || !chart.chartArea) {
    header.classList.add("hidden");
    return;
  }
  const { left, right } = chart.chartArea;
  const rightPad = Math.max(0, chart.width - right);
  track.style.marginLeft = `${Math.max(0, left)}px`;
  track.style.marginRight = `${rightPad}px`;
  header.classList.remove("hidden");
}

/* -------------------- small helper -------------------- */
async function getJSON(url) {
  const res = await fetch(url, { credentials: "same-origin" });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.json();
}

/* -------------------- dark mode -------------------- */
function isDarkMode() {
  return document.documentElement.classList.contains("dark");
}

function getChartColors() {
  return {
    text: isDarkMode() ? "#E5E7EB" : "#374151",
    grid: isDarkMode() ? "#4B5563" : "#D1D5DB",
    title: isDarkMode() ? "#F9FAFB" : "#111827",
  };
}

function initDarkModeToggle() {
  const toggle = document.getElementById("dark-mode-toggle");
  if (!toggle) return;

  if (localStorage.getItem("dark-mode") === "enabled") {
    document.documentElement.classList.add("dark");
  }

  toggle.addEventListener("click", () => {
    document.documentElement.classList.toggle("dark");
    const enabled = document.documentElement.classList.contains("dark");
    localStorage.setItem("dark-mode", enabled ? "enabled" : "disabled");

    const filteredData = filterData(
      allOrders,
      document.getElementById("search-dashboard")?.value || ""
    );
    const sortedData = sortData(filteredData, "order_date", true);
    renderTimeline(sortedData);
  });
}

/* -------------------- date helpers -------------------- */
function parseDate(dateStr) {
  try {
    if (!dateStr || typeof dateStr !== "string") throw new Error("Invalid date");

    let day, month, year;
    if (dateStr.includes(".")) {
      // dd.mm.yy
      [day, month, year] = dateStr.split(".").map(Number);
      year = year < 100 ? 2000 + year : year;
    } else if (dateStr.includes("-")) {
      // yyyy-mm-dd
      [year, month, day] = dateStr.split("-").map(Number);
    } else {
      throw new Error("Unsupported format");
    }

    const d = new Date(year, month - 1, day);
    if (isNaN(d.getTime())) throw new Error("NaN date");
    return d;
  } catch (_) {
    return null;
  }
}

function getYearFromDate(dateStr) {
  const date = parseDate(dateStr);
  return date ? date.getFullYear() : null;
}

function getWeekNumber(date) {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const dayNum = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - dayNum);
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  return Math.ceil(((d - yearStart) / 86400000 + 1) / 7);
}

function getStartOfWeek(weekNum, year) {
  const firstDayOfYear = new Date(year, 0, 1);
  const dayOfWeek = firstDayOfYear.getDay();
  const firstMonday =
    dayOfWeek === 1
      ? firstDayOfYear
      : new Date(firstDayOfYear.setDate(firstDayOfYear.getDate() + ((8 - dayOfWeek) % 7)));
  const startOfWeek = new Date(firstMonday);
  startOfWeek.setDate(startOfWeek.getDate() + (weekNum - 1) * 7);
  return startOfWeek;
}


/* -------------------- filtering -------------------- */
function filterData(data, query) {
  if (!data || !Array.isArray(data)) return [];
  query = (query || "").toLowerCase().trim();

  return data.filter((order) => {
    const orderYear = parseInt(order.delivery_year) || getYearFromDate(order.etd);
    if (!orderYear || (selectedYear && orderYear !== parseInt(selectedYear))) return false;

    if (!visibleStatuses.includes(order.transit_status)) return false;

    let orderDate = order.order_date || "";
    if (orderDate.includes("-")) {
      const [y, m, d] = orderDate.split("-");
      orderDate = `${d}.${m}.${y.slice(-2)}`;
    }
    const orderNumber = (order.order_number || "").toLowerCase();

    return query ? orderNumber.includes(query) || orderDate.toLowerCase().includes(query) : true;
  });
}

/* -------------------- timeline sort helpers -------------------- */
function sortTlData(data) {
  return [...data].sort((a, b) => {
    let va, vb;
    if (tlSortKey === "etd") {
      va = parseDate(a.etd) || new Date(0);
      vb = parseDate(b.etd) || new Date(0);
    } else {
      va = (a.product_name || "").toLowerCase();
      vb = (b.product_name || "").toLowerCase();
    }
    if (va < vb) return tlSortDir === "asc" ? -1 : 1;
    if (va > vb) return tlSortDir === "asc" ?  1 : -1;
    return 0;
  });
}

function updateTlSortUI() {
  ["date", "name"].forEach(k => {
    const arrow = document.getElementById(`tl-sort-${k}-arrow`);
    const btn   = document.getElementById(`tl-sort-${k}`);
    if (!arrow || !btn) return;
    const isActive = (k === "date" && tlSortKey === "etd") || (k === "name" && tlSortKey === "product_name");
    arrow.textContent = isActive ? (tlSortDir === "asc" ? "↑" : "↓") : "↑";
    arrow.classList.toggle("opacity-60", !isActive);
    btn.classList.toggle("border-blue-400", isActive);
    btn.classList.toggle("text-blue-600", isActive);
    btn.classList.toggle("dark:text-blue-400", isActive);
  });
}

function updateTlPaginationUI() {
  const totalPages = Math.max(1, Math.ceil(tlData.length / TL_PAGE_SIZE));
  const info  = document.getElementById("tl-page-info");
  const prev  = document.getElementById("tl-prev-btn");
  const next  = document.getElementById("tl-next-btn");
  if (info) info.textContent = tlData.length > 0 ? `Page ${tlPage} / ${totalPages}  (${tlData.length} orders)` : "";
  if (prev) prev.disabled = tlPage <= 1;
  if (next) next.disabled = tlPage >= totalPages;
  const wrap = document.querySelector(".flex.items-center.justify-between.mt-3");
  if (wrap) wrap.style.display = tlData.length > TL_PAGE_SIZE ? "" : "none";
}

/* -------------------- timeline (Chart.js) -------------------- */
function renderTimeline(data, keepPage = false) {
  // Store full sorted set for pagination
  if (!keepPage) {
    tlData = sortTlData(Array.isArray(data) ? data : []);
    tlPage = 1;
  }
  updateTlSortUI();
  updateTlPaginationUI();

  // Slice current page
  const start = (tlPage - 1) * TL_PAGE_SIZE;
  const pageData = tlData.slice(start, start + TL_PAGE_SIZE);

  const loadingIndicator = document.getElementById("timeline-loading");
  const canvas = document.getElementById("timelineChart");
  const weekHeader = document.getElementById("timeline-week-header");
  if (!canvas) return;
  ensureTimelineWeekHeader();

  if (loadingIndicator) loadingIndicator.style.display = "block";
  if (weekHeader) weekHeader.classList.add("hidden");
  canvas.style.display = "none";

  if (!Array.isArray(tlData) || tlData.length === 0) {
    if (loadingIndicator) {
      loadingIndicator.textContent = `No orders found for ${selectedYear || "selected year"}`;
      loadingIndicator.style.display = "block";
    }
    return;
  }

  // Use only the current page slice for rendering
  data = pageData;

  const year = parseInt(selectedYear) || new Date().getFullYear();
  const yearStart = new Date(year, 0, 1);
  const yearEnd = new Date(year, 11, 31);

  const chartData = [];
  const labels = [];
  let displayIndex = 0;

  data.forEach((order) => {
    const startDate = parseDate(order.etd);
    let endDate = order.ata ? parseDate(order.ata) : parseDate(order.eta);
    if (endDate) endDate.setDate(endDate.getDate() + 7);

    if (!startDate || !endDate) return;

    const orderYear = parseInt(order.delivery_year) || getYearFromDate(order.etd);
    if (orderYear !== year) return;

    const clippedStartDate = startDate < yearStart ? yearStart : startDate;
    const clippedEndDate = endDate > yearEnd ? yearEnd : endDate;

    const status = (order.transit_status || "").toLowerCase().trim();
    const color =
      {
        "in process": "rgba(255, 165, 0, 0.8)",
        "en route": "rgba(0, 123, 255, 0.8)",
        arrived: "rgba(144, 238, 144, 0.8)",
      }[status] || "rgba(128, 128, 128, 0.8)";

    chartData.push({
      x: [clippedStartDate, clippedEndDate],
      y: displayIndex,
      backgroundColor: color,
      borderColor: color.replace("0.8", "1"),
      borderWidth: 1,
    });

    const transportIconLabel = {
      sea: "⛴",
      air: "✈",
      truck: "⛟",
    }[String(order.transport || "").toLowerCase()] || "📦";
    labels.push(`${transportIconLabel} ${order.product_name} (${order.order_number})`);
    displayIndex += 1;
  });

  if (chartData.length === 0) {
    if (loadingIndicator) {
      loadingIndicator.textContent = `No valid orders found for ${selectedYear || "selected year"}`;
      loadingIndicator.style.display = "block";
    }
    canvas.style.display = "none";
    return;
  }

  const heightPerOrder = 46;
  const headerHeight = 50;
  const canvasHeight = chartData.length * heightPerOrder + headerHeight;

  // Chart.js (responsive=true, maintainAspectRatio=false) sizes the canvas by
  // reading canvas.parentNode.clientHeight — NOT canvas.style.height.
  // We wrap the canvas in an explicit-height div so Chart.js reads the right value.
  let canvasWrapper = document.getElementById("timeline-canvas-wrapper");
  if (!canvasWrapper) {
    canvasWrapper = document.createElement("div");
    canvasWrapper.id = "timeline-canvas-wrapper";
    canvasWrapper.style.position = "relative";
    canvas.parentNode.insertBefore(canvasWrapper, canvas);
    canvasWrapper.appendChild(canvas);
  }
  canvasWrapper.style.height = `${canvasHeight}px`;

  // Outer container: no scroll — pagination keeps rows ≤ TL_PAGE_SIZE
  const timelineContainer = canvasWrapper.parentElement;
  timelineContainer.style.maxHeight = "";
  timelineContainer.style.overflowY = "";
  timelineContainer.style.overflowX = "";

  if (loadingIndicator) loadingIndicator.style.display = "none";
  canvas.style.display = "block";

  const today = new Date();
  const currentWeek = getWeekNumber(today);
  const startOfWeek = getStartOfWeek(currentWeek, today.getFullYear());
  const endOfWeek = new Date(startOfWeek);
  endOfWeek.setDate(startOfWeek.getDate() + 6);

  const ctx = canvas.getContext("2d");
  if (chartInstance) chartInstance.destroy();

  const colors = getChartColors();

  chartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Orders Timeline",
          data: chartData,
          backgroundColor: chartData.map((item) => item.backgroundColor),
          borderColor: chartData.map((item) => item.borderColor),
          borderWidth: 1,
          barPercentage: 0.55,
          categoryPercentage: 0.85,
        },
      ],
    },
    options: {
      indexAxis: "y",
      scales: {
        x: {
          type: "time",
          time: { unit: "week", tooltipFormat: "dd.MM.yyyy" },
          min: yearStart,
          max: yearEnd,
          title: {
            display: false,
          },
          ticks: {
            display: false,
            color: colors.text,
            font: { size: 12, weight: "500" },
            autoSkip: true,
            maxRotation: 0,
          },
          grid: {
            color: colors.grid,
            borderColor: colors.grid,
            tickColor: colors.grid,
            lineWidth: 1,
          },
        },
        y: {
          min: 0,
          max: chartData.length - 1,
          ticks: {
            callback: (_, i) => labels[i],
            color: colors.text,
            font: { size: 12, weight: "500", lineHeight: 1.3 },
            autoSkip: false,
            padding: 5,
          },
          grid: { display: false },
        },
      },
      layout: { padding: 0 },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function (context) {
              const [start, end] = context.raw.x;
              const startDate = new Date(start).toLocaleDateString();
              const endDate = new Date(end).toLocaleDateString();
              return `Delivery: ${startDate} в†’ ${endDate}`;
            },
          },
        },
        annotation: {
          annotations: {
            currentWeek: {
              type: "box",
              xMin: startOfWeek,
              xMax: endOfWeek,
              yMin: 0,
              yMax: chartData.length - 1,
              backgroundColor: "rgba(255,255,0,0.3)",
              borderColor: "rgba(255,255,0,0.6)",
              label: {
                enabled: true,
                content: `W${currentWeek}`,
                position: "top",
              },
            },
          },
        },
      },
      responsive: true,
      maintainAspectRatio: false,
    },
  });
  requestAnimationFrame(() => syncTimelineWeekHeader(chartInstance));
}

/* -------------------- sorting -------------------- */
function sortData(data, key, forceDescending = false) {
  if (!sortDirection[key]) sortDirection[key] = "desc";
  if (!forceDescending) sortDirection[key] = sortDirection[key] === "asc" ? "desc" : "asc";
  const direction = forceDescending ? "desc" : sortDirection[key];
  lastSortKey = key;
  lastSortDirection = direction;

  document.querySelectorAll("th[data-sort]").forEach((th) => {
    const thKey = th.getAttribute("data-sort");
    const indicator = th.querySelector(".sort-indicator");
    const isActive = thKey === key;
    if (indicator) indicator.textContent = isActive ? (direction === "asc" ? "↑" : "↓") : "";
    th.classList.toggle("th-sort-active", isActive);
  });

  return [...data].sort((a, b) => {
    let valA = a[key] || "";
    let valB = b[key] || "";
    if (["order_date", "required_delivery", "payment_date", "etd", "eta", "ata"].includes(key)) {
      valA = parseDate(valA) || new Date(0);
      valB = parseDate(valB) || new Date(0);
    } else if (key === "quantity") {
      valA = parseFloat(valA) || 0;
      valB = parseFloat(valB) || 0;
    } else {
      valA = valA.toString().toLowerCase();
      valB = valB.toString().toLowerCase();
    }
    return direction === "asc" ? (valA > valB ? 1 : -1) : (valA < valB ? 1 : -1);
  });
}

/* -------------------- DOM ready -------------------- */
document.addEventListener("DOMContentLoaded", function () {
  const orderDateHeader = document.querySelector('th[data-sort="order_date"]');
  if (orderDateHeader) {
    const indicator = orderDateHeader.querySelector(".sort-indicator");
    if (indicator) indicator.textContent = "v";
  }

  Chart.register(window["chartjs-plugin-annotation"]);
  initDarkModeToggle();

  /* ---------- products select (TomSelect) ---------- */
  const initializeProductSelect = () => {
    const selectEl = document.getElementById("product_name");
    if (!selectEl) return;

    fetch("/api/products")
      .then((res) => res.json())
      .then((products) => {
        if (selectEl.tomselect) selectEl.tomselect.destroy();
        selectEl.innerHTML = "";
        products.forEach((p) => {
          const opt = document.createElement("option");
          opt.value = p;
          opt.textContent = p;
          selectEl.appendChild(opt);
        });
        new TomSelect(selectEl, {
          create: true,
          sortField: { field: "text", direction: "asc" },
          maxOptions: 200,
        });
      })
      .catch((err) => console.error("products load error:", err));
  };
  initializeProductSelect();

  /* ---------- KPI cards ---------- */
  (function loadKpi() {
    fetch("/api/kpi")
      .then((r) => r.json())
      .then((data) => {
        const cards = [
          { key: "in_transit", countId: "kpi-transit-count",   deltaId: "kpi-transit-delta"   },
          { key: "warehouse",  countId: "kpi-warehouse-count", deltaId: "kpi-warehouse-delta"  },
          { key: "delivered",  countId: "kpi-delivered-count", deltaId: "kpi-delivered-delta"  },
          { key: "delayed",    countId: "kpi-delayed-count",   deltaId: "kpi-delayed-delta"    },
        ];

        cards.forEach(({ key, countId, deltaId }) => {
          const metric = data[key];
          if (!metric) return;

          const countEl = document.getElementById(countId);
          const deltaEl = document.getElementById(deltaId);
          if (countEl) countEl.textContent = metric.count;

          if (!deltaEl) return;
          const pct = metric.delta_pct;
          if (pct === null || pct === undefined) {
            deltaEl.textContent = metric.delta_label || "";
            deltaEl.className = "text-xs text-gray-400 dark:text-gray-500";
            return;
          }

          const isGood = metric.positive_is_good ? pct >= 0 : pct <= 0;
          const arrow  = pct > 0 ? "↑" : pct < 0 ? "↓" : "→";
          const sign   = pct > 0 ? "+" : "";
          const color  = pct === 0
            ? "text-gray-400 dark:text-gray-500"
            : isGood
              ? "text-emerald-500 dark:text-emerald-400"
              : "text-red-500 dark:text-red-400";

          deltaEl.innerHTML =
            `<span class="${color} font-medium">${arrow} ${sign}${pct}%</span>` +
            ` <span class="text-gray-400 dark:text-gray-500">${metric.delta_label}</span>`;
          deltaEl.className = "text-xs";
        });
      })
      .catch((err) => console.error("kpi load error:", err));
  })();

  /* ---------- YEAR + ORDERS loading via new APIs ---------- */

  // 1) Insert years into the dropdown
  function populateYearDropdownFromAPI(years) {
    const yearFilter = document.getElementById("year-filter");
    if (!yearFilter) return;

    yearFilter.innerHTML = "";
    if (!years || years.length === 0) {
      yearFilter.innerHTML = '<option value="" disabled selected>No orders available</option>';
      selectedYear = null;
      return;
    }
    years.forEach((y) => {
      const opt = document.createElement("option");
      opt.value = y;
      opt.textContent = y;
      yearFilter.appendChild(opt);
    });

    // default to the first entry (API already returns sorted; if not, this is still fine)
    if (!selectedYear || !years.includes(parseInt(selectedYear))) {
      selectedYear = years[0];
      yearFilter.value = selectedYear;
    } else {
      yearFilter.value = selectedYear;
    }
  }

  // 2) Fetch orders for the selected year
  async function loadOrdersForYear(year) {
    try {
      const data = await getJSON(`/api/orders?year=${encodeURIComponent(year)}`);
      const rows = data.orders || [];

      // normalize incoming rows for the existing UI
      allOrders = rows.map((order) => ({
        ...order,
        order_date: order.order_date && order.order_date.includes("-")
          ? order.order_date.split("-").reverse().join(".")
          : order.order_date || "",
        etd: order.etd && order.etd.includes("-")
          ? order.etd.split("-").reverse().join(".")
          : order.etd || "",
        eta: order.eta && order.eta.includes("-")
          ? order.eta.split("-").reverse().join(".")
          : order.eta || "",
        ata: order.ata && order.ata.includes("-")
          ? order.ata.split("-").reverse().join(".")
          : order.ata || "",
        required_delivery: order.required_delivery && order.required_delivery.includes("-")
          ? order.required_delivery.split("-").reverse().join(".")
          : order.required_delivery || "",
        payment_date: order.payment_date && order.payment_date.includes("-")
          ? order.payment_date.split("-").reverse().join(".")
          : order.payment_date || "",
        delivery_year: parseInt(year) || null,
      }));

      const yearWarning = document.getElementById("year-warning");
      if (yearWarning) yearWarning.classList.add("hidden");

      if (!selectedYear) {
        updateTable([]);
        renderTimeline([]);
        return;
      }

      const filteredData = filterData(
        allOrders,
        document.getElementById("search-dashboard")?.value || ""
      );
      const sortedData = sortData(filteredData, lastSortKey, lastSortDirection === "desc");
      updateTable(sortedData);
      renderTimeline(sortedData);
    } catch (err) {
      console.error("loadOrdersForYear error:", err);
      updateTable([]);
      renderTimeline([]);
    }
  }

  // 3) Initial bootstrap: years -> selectedYear -> orders
  async function bootstrapYearsAndOrders() {
    try {
      const { years } = await getJSON("/api/years");
      populateYearDropdownFromAPI(years || []);
      if (selectedYear) await loadOrdersForYear(selectedYear);
    } catch (err) {
      console.error("bootstrapYearsAndOrders error:", err);
      populateYearDropdownFromAPI([]);
      updateTable([]);
      renderTimeline([]);
    }
  }

  // в†“ This replaced the previous "fetchAndRender" that called /api/orders with no year
  bootstrapYearsAndOrders();

  // Timeline pagination buttons
  const tlPrevBtn = document.getElementById("tl-prev-btn");
  const tlNextBtn = document.getElementById("tl-next-btn");
  if (tlPrevBtn) {
    tlPrevBtn.addEventListener("click", () => {
      if (tlPage > 1) { tlPage -= 1; renderTimeline(null, true); }
    });
  }
  if (tlNextBtn) {
    tlNextBtn.addEventListener("click", () => {
      const totalPages = Math.max(1, Math.ceil(tlData.length / TL_PAGE_SIZE));
      if (tlPage < totalPages) { tlPage += 1; renderTimeline(null, true); }
    });
  }

  // Timeline sort buttons
  document.getElementById("tl-sort-date")?.addEventListener("click", () => {
    if (tlSortKey === "etd") {
      tlSortDir = tlSortDir === "asc" ? "desc" : "asc";
    } else {
      tlSortKey = "etd";
      tlSortDir = "asc";
    }
    tlData = sortTlData(tlData);
    tlPage = 1;
    renderTimeline(null, true);
  });

  document.getElementById("tl-sort-name")?.addEventListener("click", () => {
    if (tlSortKey === "product_name") {
      tlSortDir = tlSortDir === "asc" ? "desc" : "asc";
    } else {
      tlSortKey = "product_name";
      tlSortDir = "asc";
    }
    tlData = sortTlData(tlData);
    tlPage = 1;
    renderTimeline(null, true);
  });

  const firstPageBtn = document.getElementById("orders-first-page");
  const prevPageBtn = document.getElementById("orders-prev-page");
  const nextPageBtn = document.getElementById("orders-next-page");
  const lastPageBtn = document.getElementById("orders-last-page");
  if (firstPageBtn) {
    firstPageBtn.addEventListener("click", () => {
      if (currentPage !== 1) {
        currentPage = 1;
        renderTablePage();
      }
    });
  }
  if (prevPageBtn) {
    prevPageBtn.addEventListener("click", () => {
      if (currentPage > 1) {
        currentPage -= 1;
        renderTablePage();
      }
    });
  }
  if (nextPageBtn) {
    nextPageBtn.addEventListener("click", () => {
      const totalPages = Math.max(1, Math.ceil(currentTableData.length / pageSize));
      if (currentPage < totalPages) {
        currentPage += 1;
        renderTablePage();
      }
    });
  }
  if (lastPageBtn) {
    lastPageBtn.addEventListener("click", () => {
      const totalPages = Math.max(1, Math.ceil(currentTableData.length / pageSize));
      if (currentPage !== totalPages) {
        currentPage = totalPages;
        renderTablePage();
      }
    });
  }

  function formatQuantity(value) {
    const parsed = parseFloat(value);
    return Number.isFinite(parsed) ? parsed.toFixed(2) : "-";
  }

  function statusBadge(status) {
    const s = (status || "").toLowerCase().trim();
    const styles = {
      "in process": "background:rgba(255,165,0,0.15);color:#b45309;border:1px solid rgba(255,165,0,0.4)",
      "en route":   "background:rgba(0,123,255,0.12);color:#1d4ed8;border:1px solid rgba(0,123,255,0.35)",
      "arrived":    "background:rgba(56,200,100,0.13);color:#166534;border:1px solid rgba(56,200,100,0.4)",
    };
    const style = styles[s] || "background:#f3f4f6;color:#6b7280;border:1px solid #d1d5db";
    const label = status ? status.charAt(0).toUpperCase() + status.slice(1) : "-";
    return `<span style="${style};display:inline-flex;align-items:center;padding:2px 8px;border-radius:9999px;font-size:10px;font-weight:600;letter-spacing:0.04em;text-transform:uppercase;white-space:nowrap">${label}</span>`;
  }

  function renderTableRows(rows) {
    const tbody = document.querySelector("table tbody");
    if (!tbody) return;
    tbody.innerHTML = "";

    if (!rows || rows.length === 0) {
      const row = document.createElement("tr");
      row.innerHTML =
        `<td colspan="15" class="px-2 py-1 sm:px-4 sm:py-2 text-xs sm:text-sm text-gray-800 dark:text-gray-200 text-center">No orders found</td>`;
      tbody.appendChild(row);
      lucide.createIcons();
      return;
    }

    rows.forEach((order) => {
      const transportRaw = String(order.transport || "").toLowerCase();
      const transportIcon =
        transportRaw === "sea"
          ? '<i data-lucide="ship" class="w-4 h-4 inline-block"></i>'
          : transportRaw === "air"
            ? '<i data-lucide="plane" class="w-4 h-4 inline-block"></i>'
            : transportRaw === "truck"
              ? '<i data-lucide="truck" class="w-4 h-4 inline-block"></i>'
              : '<i data-lucide="package" class="w-4 h-4 inline-block"></i>';
      const row = document.createElement("tr");
      row.classList.add("bg-gray-100","dark:bg-gray-900","hover:bg-gray-200","dark:hover:bg-gray-700");

      row.innerHTML = `
        <td class="px-2 py-1 text-[11px] sm:text-xs text-gray-800 dark:text-gray-200 whitespace-nowrap" title="Delivery Year: ${order.delivery_year}">${order.order_date || "-"}</td>
        <td class="px-2 py-1 text-[11px] sm:text-xs text-gray-800 dark:text-gray-200 whitespace-nowrap">${order.order_number || "-"}</td>
        <td class="px-2 py-1 text-[11px] sm:text-xs text-gray-800 dark:text-gray-200 whitespace-nowrap">${order.product_name || "-"}</td>
        <td class="px-2 py-1 text-[11px] sm:text-xs text-gray-800 dark:text-gray-200 whitespace-nowrap">${order.buyer || "-"}</td>
        <td class="px-2 py-1 text-[11px] sm:text-xs text-gray-800 dark:text-gray-200 whitespace-nowrap">${order.responsible || "-"}</td>
        <td class="px-2 py-1 text-[11px] sm:text-xs text-gray-800 dark:text-gray-200 whitespace-nowrap">${formatQuantity(order.quantity)}</td>
        <td class="px-2 py-1 text-[11px] sm:text-xs text-gray-800 dark:text-gray-200 whitespace-nowrap">${order.required_delivery || "-"}</td>
        <td class="px-2 py-1 text-[11px] sm:text-xs text-gray-800 dark:text-gray-200 whitespace-nowrap">${order.terms_of_delivery || "-"}</td>
        <td class="px-2 py-1 text-[11px] sm:text-xs text-gray-800 dark:text-gray-200 whitespace-nowrap">${order.payment_date || "-"}</td>
        <td class="px-2 py-1 text-[11px] sm:text-xs text-gray-800 dark:text-gray-200 whitespace-nowrap">${order.etd || "-"}</td>
        <td class="px-2 py-1 text-[11px] sm:text-xs text-gray-800 dark:text-gray-200 whitespace-nowrap">${order.eta || "-"}</td>
        <td class="px-2 py-1 text-[11px] sm:text-xs text-gray-800 dark:text-gray-200 whitespace-nowrap">${order.ata || ""}</td>
        <td class="px-2 py-1 whitespace-nowrap">${statusBadge(order.transit_status)}</td>
        <td class="px-2 py-1 text-[11px] sm:text-xs text-gray-800 dark:text-gray-200 whitespace-nowrap">${transportIcon}</td>
        <td class="px-2 py-1 text-center">
          <div class="flex items-center justify-center gap-0.5">
            ${
              window.currentUserRole !== "superuser"
                ? `
              <button type="button" class="edit-order action-icon-btn hover:text-blue-400 hover:bg-blue-400/10" data-id="${order.id}" title="Edit">
                <i data-lucide="pencil" class="w-3.5 h-3.5"></i>
              </button>
              <button type="button" class="delete-order action-icon-btn hover:text-red-400 hover:bg-red-400/10" data-id="${order.id}" title="Delete">
                <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
              </button>
              ${
                order.transit_status === "arrived"
                  ? `
                <form method="POST" action="/stock_order/${order.id}" style="display:contents">
                  <button type="submit" class="action-icon-btn hover:text-amber-400 hover:bg-amber-400/10" title="Move to Warehouse">
                    <i data-lucide="warehouse" class="w-3.5 h-3.5"></i>
                  </button>
                </form>
                <form method="POST" action="/deliver_direct/${order.id}" style="display:contents">
                  <button type="submit" class="action-icon-btn hover:text-emerald-400 hover:bg-emerald-400/10" title="Mark as Delivered">
                    <i data-lucide="check-circle" class="w-3.5 h-3.5"></i>
                  </button>
                </form>
                `
                  : ""
              }
              `
                : ""
            }
          </div>
        </td>
      `;
      tbody.appendChild(row);
    });

    lucide.createIcons();
    attachActionHandlers();
  }

  function updatePaginationControls() {
    const bar = document.getElementById("dashboard-pagination");
    const first = document.getElementById("orders-first-page");
    const prev = document.getElementById("orders-prev-page");
    const next = document.getElementById("orders-next-page");
    const last = document.getElementById("orders-last-page");
    const label = document.getElementById("orders-page-label");
    if (!bar || !first || !prev || !next || !last || !label) return;

    const total = currentTableData.length;
    const pages = Math.max(1, Math.ceil(total / pageSize));

    if (total <= pageSize) {
      bar.classList.add("hidden");
      return;
    }

    bar.classList.remove("hidden");
    first.disabled = currentPage <= 1;
    prev.disabled = currentPage <= 1;
    next.disabled = currentPage >= pages;
    last.disabled = currentPage >= pages;
    label.textContent = `Page ${currentPage} / ${pages} (${total} rows)`;
  }

  function renderTablePage() {
    if (!currentTableData || currentTableData.length === 0) {
      renderTableRows([]);
      const bar = document.getElementById("dashboard-pagination");
      if (bar) bar.classList.add("hidden");
      return;
    }

    const totalPages = Math.max(1, Math.ceil(currentTableData.length / pageSize));
    if (currentPage > totalPages) currentPage = totalPages;
    if (currentPage < 1) currentPage = 1;

    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;
    renderTableRows(currentTableData.slice(start, end));
    updatePaginationControls();
  }

  function fitOrdersTableToViewport() {
    const container = document.getElementById("orders-table-container");
    if (!container) return;

    const rect = container.getBoundingClientRect();
    const footerReserve = 76; // pagination and breathing room
    const available = Math.max(360, window.innerHeight - rect.top - footerReserve);
    container.style.height = `${available}px`;
    container.style.overflowY = "auto";
    updatePaginationControls();
  }

  /* ---------- table render ---------- */
  function updateTable(data, keepPage = false) {
    currentTableData = Array.isArray(data) ? data : [];
    pageSize = PAGE_SIZE_FIXED;
    if (!keepPage) currentPage = 1;
    renderTablePage();
    fitOrdersTableToViewport();
  }

  window.addEventListener("resize", fitOrdersTableToViewport);

  /* ---------- sorting clicks ---------- */
  document.querySelectorAll("table th[data-sort]").forEach((header) => {
    header.addEventListener("click", () => {
      const key = header.getAttribute("data-sort");
      const filteredData = filterData(
        allOrders,
        document.getElementById("search-dashboard")?.value || ""
      );
      const sortedData = sortData(filteredData, key);
      updateTable(sortedData);
      renderTimeline(sortedData);
    });
  });

  /* ---------- free text filter ---------- */
  const orderFilterInput = document.getElementById("search-dashboard");
  if (orderFilterInput) {
    orderFilterInput.addEventListener("input", (e) => {
      const query = e.target.value;
      const filteredData = filterData(allOrders, query);
      const sortedData = sortData(filteredData, "order_date", true);
      updateTable(sortedData);
      renderTimeline(sortedData);
    });
  }

  /* ---------- year change => reload from /api/orders?year= ---------- */
  const yearFilterEl = document.getElementById("year-filter");
  if (yearFilterEl) {
    yearFilterEl.addEventListener("change", async (e) => {
      selectedYear = e.target.value;
      sortDirection = { order_date: "desc" };
      const orderDateHeader = document.querySelector('th[data-sort="order_date"]');
      if (orderDateHeader) {
        const indicator = orderDateHeader.querySelector(".sort-indicator");
        if (indicator) indicator.textContent = "v";
      }
      document.querySelectorAll("th[data-sort]").forEach((th) => {
        if (th.getAttribute("data-sort") !== "order_date") {
          const indicator = th.querySelector(".sort-indicator");
          if (indicator) indicator.textContent = "";
        }
      });
      await loadOrdersForYear(selectedYear);
    });
  }

  /* ---------- legend toggle ---------- */
  document.querySelectorAll(".legend-item").forEach((item) => {
    item.addEventListener("click", () => {
      const status = item.getAttribute("data-status");
      if (visibleStatuses.includes(status)) {
        visibleStatuses = visibleStatuses.filter((s) => s !== status);
        item.classList.add("opacity-50");
      } else {
        visibleStatuses.push(status);
        item.classList.remove("opacity-50");
      }
      const filteredData = filterData(
        allOrders,
        document.getElementById("search-dashboard")?.value || ""
      );
      const sortedData = sortData(filteredData, "order_date", true);
      updateTable(sortedData);
      renderTimeline(sortedData);
    });
  });

  /* ---------- add/edit/delete handlers (unchanged) ---------- */
  const addForm = document.getElementById("add-order-form");
  if (addForm) {
    addForm.addEventListener("submit", async function (event) {
      event.preventDefault();

      const quantity = parseFloat(document.getElementById("quantity").value);
      const orderDate = document.getElementById("order_date").value;
      const etd = document.getElementById("etd").value;
      const eta = document.getElementById("eta").value;
      const requiredDelivery = document.getElementById("required_delivery").value;

      if (!requiredDelivery.trim()) return showFormNotify("Required Delivery cannot be empty.", "error");
      if (isNaN(quantity) || quantity <= 0) return showFormNotify("Quantity must be a positive number.", "error");
      if (etd && orderDate && orderDate > etd) return showFormNotify("Order Date cannot be later than ETD.", "error");
      if (etd && eta && etd > eta) return showFormNotify("ETD cannot be later than ETA.", "error");

      const submitBtn = document.getElementById("add-order-submit");
      const btnSpan = submitBtn?.querySelector("span");
      const btnIcon = submitBtn?.querySelector("i[data-lucide]");
      if (submitBtn) {
        submitBtn.disabled = true;
        if (btnSpan) btnSpan.textContent = "Saving…";
        if (btnIcon) btnIcon.setAttribute("data-lucide", "loader-2");
        lucide.createIcons({ nodes: submitBtn ? [submitBtn] : [] });
      }

      const formData = new FormData(addForm);
      const dateFields = ["order_date","required_delivery","payment_date","etd","eta","ata"];
      const converted = new FormData();
      for (let [k, v] of formData.entries()) {
        if (dateFields.includes(k) && /^\d{4}-\d{2}-\d{2}$/.test(v)) {
          const [y, m, d] = v.split("-");
          v = `${d}.${m}.${y.slice(2)}`;
        }
        converted.append(k, v);
      }

      try {
        const r = await fetch("/add_order", { method: "POST", body: converted });
        const data = await r.json();
        if (data.success) {
          showFormNotify("Order added successfully!", "success");
          addForm.reset();
          await loadOrdersForYear(selectedYear);
          // Auto-close after a short pause so user sees the success message
          setTimeout(closeAddOrderForm, 1800);
        } else {
          showFormNotify("Error: " + (data.message || "Unknown error"), "error");
        }
      } catch (err) {
        console.error("add error", err);
        showFormNotify("Network error — please try again.", "error");
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          if (btnSpan) btnSpan.textContent = "Add Order";
          if (btnIcon) btnIcon.setAttribute("data-lucide", "plus-circle");
          lucide.createIcons({ nodes: submitBtn ? [submitBtn] : [] });
        }
      }
    });
  }

  document.addEventListener("click", function (event) {
    if (event.target.classList.contains("edit-order")) {
      event.preventDefault();
      const orderId = event.target.getAttribute("data-id");
      fetch(`/api/orders?year=${encodeURIComponent(selectedYear)}`)
        .then((response) => response.json())
        .then((payload) => {
          const data = payload.orders || [];
          const order = data.find((o) => o.id == orderId);
          if (order) {
            document.getElementById("edit-order-id").value = order.id;
            const dateFields = ["order_date","required_delivery","payment_date","etd","eta","ata"];
            dateFields.forEach((field) => {
              const value = order[field];
              const input = document.getElementById(`edit-${field}`);
              if (input) {
                const date = parseDate(value);
                input.value = date ? date.toISOString().split("T")[0] : "";
              }
            });

            document.getElementById("edit-order_number").value = order.order_number;
            const productSelect = document.getElementById("edit-product_name");

            if (productSelect) {
              fetch("/api/products")
                .then((res) => res.json())
                .then((products) => {
                  if (productSelect.tomselect) productSelect.tomselect.destroy();
                  productSelect.innerHTML = "";
                  const allProducts = [...new Set([order.product_name, ...products])];
                  allProducts.forEach((p) => {
                    const opt = document.createElement("option");
                    opt.value = p;
                    opt.textContent = p;
                    productSelect.appendChild(opt);
                  });
                  const tom = new TomSelect(productSelect, {
                    create: true,
                    sortField: { field: "text", direction: "asc" },
                    maxOptions: 200,
                  });
                  tom.setValue(order.product_name);
                });
            }

            document.getElementById("edit-buyer").value = order.buyer;
            document.getElementById("edit-responsible").value = order.responsible;
            document.getElementById("edit-quantity").value = order.quantity;
            document.getElementById("edit-terms_of_delivery").value = order.terms_of_delivery;
            document.getElementById("edit-transit_status").value = order.transit_status;
            document.getElementById("edit-transport").value = order.transport;
            document.getElementById("edit-order-modal").style.display = "flex";
          }
        });
    }

    if (event.target.classList.contains("delete-order")) {
      event.preventDefault();
      if (!confirm("Are you sure you want to delete this order?")) return;

      const orderId = event.target.getAttribute("data-id");
      fetch(`/delete_order/${orderId}`, { method: "GET" })
        .then((r) => r.json())
        .then(async (data) => {
          if (data.success) {
            alert("Order deleted successfully!");
            await loadOrdersForYear(selectedYear);
          } else {
            alert("Error deleting order: " + (data.message || "Unknown error"));
          }
        })
        .catch((err) => {
          console.error("delete error", err);
          alert("Error deleting order. Please try again.");
        });
    }
  });

  const editForm = document.getElementById("edit-order-form");
  if (editForm) {
    editForm.addEventListener("submit", function (event) {
      event.preventDefault();

      const quantity = parseFloat(document.getElementById("edit-quantity").value);
      const orderDate = document.getElementById("edit-order_date").value;
      const etd = document.getElementById("edit-etd").value;
      const eta = document.getElementById("edit-eta").value;

      if (isNaN(quantity) || quantity <= 0) return alert("Quantity must be positive.");
      if (etd && orderDate && orderDate > etd) return alert("Order Date cannot be later than ETD.");
      if (etd && eta && etd > eta) return alert("ETD cannot be later than ETA.");

      const formData = new FormData(editForm);
      const dateFields = ["order_date","required_delivery","payment_date","etd","eta","ata"];
      const converted = new FormData();
      for (let [k, v] of formData.entries()) {
        if (dateFields.includes(k) && /^\d{4}-\d{2}-\d{2}$/.test(v)) {
          const [y, m, d] = v.split("-");
          v = `${d}.${m}.${y.slice(2)}`;
        }
        converted.append(k, v);
      }

      const orderId = document.getElementById("edit-order-id").value;
      fetch(`/edit_order/${orderId}`, { method: "POST", body: converted })
        .then((r) => r.json())
        .then(async (data) => {
          if (data.success) {
            alert("Order updated successfully!");
            editForm.reset();
            document.getElementById("edit-order-modal").style.display = "none";
            await loadOrdersForYear(selectedYear);
          } else {
            alert("Error editing order: " + (data.message || "Unknown error"));
          }
        })
        .catch((err) => {
          console.error("edit error", err);
          alert("Error editing order. Please try again.");
        });
    });
  }

  const closeButton = document.querySelector(".close");
  if (closeButton) {
    closeButton.addEventListener("click", function () {
      document.getElementById("edit-order-modal").style.display = "none";
    });
  }

  window.addEventListener("click", function (event) {
    const modal = document.getElementById("edit-order-modal");
    if (event.target === modal) modal.style.display = "none";
  });

  /* ── Add-order form helpers ─────────────────────────── */
  function nextOrderNumber() {
    const yyyy = new Date().getFullYear();
    const n = Number(localStorage.getItem("demo_po_counter") || "100") + 1;
    localStorage.setItem("demo_po_counter", String(n));
    return `PO-${yyyy}-${String(n).padStart(3, "0")}`;
  }

  function showFormNotify(msg, type) {
    const el = document.getElementById("order-form-notify");
    if (!el) return;
    el.textContent = msg;
    el.className = "form-notify " + (type === "error" ? "form-notify-error" : "form-notify-success");
    el.style.display = "block";
    if (type === "success") {
      clearTimeout(el._notifyTimer);
      el._notifyTimer = setTimeout(() => { el.style.display = "none"; }, 4000);
    }
  }

  function closeAddOrderForm() {
    const section = document.getElementById("add-order-section");
    const form = document.getElementById("add-order-form");
    const btn = document.querySelector(".toggle-form-btn");
    if (section) section.style.display = "none";
    if (form) form.reset();
    const notifyEl = document.getElementById("order-form-notify");
    if (notifyEl) notifyEl.style.display = "none";
    if (btn) {
      btn.querySelector(".btn-icon-open")?.classList.remove("hidden");
      btn.querySelector(".btn-icon-close")?.classList.add("hidden");
      const span = btn.querySelector("span");
      if (span) span.textContent = "New Order";
    }
  }

  /* ── Toggle form open/close ─────────────────────────── */
  const toggleFormBtn = document.querySelector(".toggle-form-btn");
  const addOrderSection = document.getElementById("add-order-section");
  if (toggleFormBtn && addOrderSection) {
    toggleFormBtn.addEventListener("click", () => {
      const isHidden =
        addOrderSection.style.display === "none" || addOrderSection.style.display === "";
      if (isHidden) {
        addOrderSection.style.display = "block";
        toggleFormBtn.querySelector(".btn-icon-open")?.classList.add("hidden");
        toggleFormBtn.querySelector(".btn-icon-close")?.classList.remove("hidden");
        const span = toggleFormBtn.querySelector("span");
        if (span) span.textContent = "Close";
        initializeProductSelect();
        // Pre-fill order number once on open
        const orderInput = document.getElementById("order_number");
        if (orderInput && !orderInput.value) orderInput.value = nextOrderNumber();
      } else {
        closeAddOrderForm();
      }
    });
  }

  /* ── Close via × button and Cancel button ───────────── */
  document.getElementById("close-add-order")?.addEventListener("click", closeAddOrderForm);
  document.getElementById("cancel-add-order")?.addEventListener("click", closeAddOrderForm);

  window.addEventListener("resize", () => {
    fitOrdersTableToViewport();
    const filteredData = filterData(
      allOrders,
      document.getElementById("search-dashboard")?.value || ""
    );
    const sortedData = sortData(filteredData, lastSortKey, lastSortDirection === "desc");
    renderTimeline(sortedData);
  });

  function attachActionHandlers() {
    document.querySelectorAll(".edit-order").forEach((btn) => {
      btn.addEventListener("click", () => {
        const orderId = btn.dataset.id;
        window.location.href = `/edit_order/${orderId}`;
      });
    });

    document.querySelectorAll(".delete-order").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const orderId = btn.dataset.id;
        if (confirm("Are you sure you want to delete this order?")) {
          try {
            const response = await fetch(`/delete_order/${orderId}`, {
              method: "POST",
              headers: { "X-Requested-With": "XMLHttpRequest" },
            });
            if (response.ok) {
              await loadOrdersForYear(selectedYear);
            } else {
              alert("Error deleting order.");
            }
          } catch (err) {
            console.error("Delete failed", err);
          }
        }
      });
    });
  }
});

