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

/* -------------------- timeline (Chart.js) -------------------- */
function renderTimeline(data) {
  const loadingIndicator = document.getElementById("timeline-loading");
  const canvas = document.getElementById("timelineChart");
  if (!canvas) return;

  if (loadingIndicator) loadingIndicator.style.display = "block";
  canvas.style.display = "none";

  if (!Array.isArray(data) || data.length === 0) {
    if (loadingIndicator) {
      loadingIndicator.textContent =
        data.length === 0
          ? `No orders found for ${selectedYear || "selected year"}`
          : "Loading...";
      loadingIndicator.style.display = "block";
    }
  }

  if (!Array.isArray(data) || data.length === 0) return;

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

    const transportLabel = {
      sea: "SEA",
      air: "AIR",
      truck: "TRK",
    }[String(order.transport || "").toLowerCase()] || (order.transport || "N/A");
    labels.push(`${transportLabel} ${order.product_name} (${order.order_number})`);
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

  const heightPerOrder = 30;
  const headerHeight = 50;
  const canvasHeight = Math.max(200, chartData.length * heightPerOrder + headerHeight);
  const timelineContainer = canvas.parentElement;
  timelineContainer.style.height = `${canvasHeight}px`;
  canvas.style.height = `${canvasHeight}px`;

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
            display: true,
            text: "Timeline",
            font: { size: 16, weight: "600" },
            color: colors.title,
          },
          ticks: {
            callback: (value) => `W${getWeekNumber(new Date(value))}`,
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
            font: { size: 16, weight: "500" },
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
    if (indicator) indicator.textContent = thKey === key ? (direction === "asc" ? "^" : "v") : "";
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
        <td class="px-2 py-1 text-[11px] sm:text-xs text-gray-800 dark:text-gray-200 whitespace-nowrap">${order.transit_status || "-"}</td>
        <td class="px-2 py-1 text-[11px] sm:text-xs text-gray-800 dark:text-gray-200 whitespace-nowrap">${transportIcon}</td>
        <td class="px-2 py-2 text-center text-xs sm:text-sm">
          <div class="flex flex-col sm:flex-row sm:justify-center gap-1 sm:gap-2">
            ${
              window.currentUserRole !== "superuser"
                ? `
              <button type="button" class="edit-order text-blue-600 hover:text-blue-800" data-id="${order.id}" title="Edit Order"><i data-lucide="pencil" class="w-4 h-4"></i></button>
              <button type="button" class="delete-order text-red-600 hover:text-red-800" data-id="${order.id}" title="Delete Order"><i data-lucide="trash-2" class="w-4 h-4"></i></button>
              ${
                order.transit_status === "arrived"
                  ? `
                <form method="POST" action="/stock_order/${order.id}">
                  <button type="submit" class="text-yellow-600 hover:text-yellow-800" title="Move to Warehouse"><i data-lucide="warehouse" class="w-4 h-4"></i></button>
                </form>
                <form method="POST" action="/deliver_direct/${order.id}">
                  <button type="submit" class="text-green-600 hover:text-green-800" title="Mark as Delivered"><i data-lucide="truck" class="w-4 h-4"></i></button>
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
    container.style.overflowY = "hidden";
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
    addForm.addEventListener("submit", function (event) {
      event.preventDefault();

      const quantity = parseFloat(document.getElementById("quantity").value);
      const orderDate = document.getElementById("order_date").value;
      const etd = document.getElementById("etd").value;
      const eta = document.getElementById("eta").value;
      const requiredDelivery = document.getElementById("required_delivery").value;

      if (!requiredDelivery.trim()) return alert("Required Delivery cannot be empty.");
      if (isNaN(quantity) || quantity <= 0) return alert("Quantity must be a positive number.");
      if (etd && orderDate && orderDate > etd) return alert("Order Date cannot be later than ETD.");
      if (etd && eta && etd > eta) return alert("ETD cannot be later than ETA.");

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

      fetch("/add_order", { method: "POST", body: converted })
        .then((r) => r.json())
        .then(async (data) => {
          if (data.success) {
            alert("Order added successfully!");
            addForm.reset();
            await loadOrdersForYear(selectedYear); // refresh
          } else {
            alert("Error adding order: " + (data.message || "Unknown error"));
          }
        })
        .catch((err) => {
          console.error("add error", err);
          alert("Error adding order. Please try again.");
        });
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

  const toggleFormBtn = document.querySelector(".toggle-form-btn");
  const addOrderSection = document.getElementById("add-order-section");
  if (toggleFormBtn && addOrderSection) {
    toggleFormBtn.addEventListener("click", () => {
      const isHidden =
        addOrderSection.style.display === "none" || addOrderSection.style.display === "";
      addOrderSection.style.display = isHidden ? "block" : "none";
      toggleFormBtn.textContent = isHidden ? "Hide Add Order Form" : "Add New Order";
      if (isHidden) initializeProductSelect();
    });
  }

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

