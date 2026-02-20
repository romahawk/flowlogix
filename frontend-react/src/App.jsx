import { useEffect, useMemo, useState } from "react";
import AppShell from "./components/AppShell";
import EmptyState from "./components/EmptyState";
import ErrorBanner from "./components/ErrorBanner";
import LoadingSkeleton from "./components/LoadingSkeleton";
import OrdersTable from "./components/OrdersTable";
import OrdersToolbar from "./components/OrdersToolbar";
import Pagination from "./components/Pagination";
import TimelineGantt from "./components/TimelineGantt";
import { getAuthMe, getOrders, postLegacyAction } from "./lib/api";
import {
  DEFAULT_QUERY,
  readQueryState,
  withPageReset,
  writeQueryState,
} from "./lib/queryState";

function Unauthorized() {
  return (
    <section className="unauthorized">
      <h2>Session required</h2>
      <p>Please sign in with your existing FlowLogix account.</p>
      <a href="/login">Go to login</a>
    </section>
  );
}

function normalizeStatus(value) {
  return String(value || "").toLowerCase().replace("_", " ").trim();
}

function inferBackendBase() {
  const fromEnv = import.meta.env.VITE_BACKEND_ORIGIN;
  if (fromEnv && fromEnv.trim()) {
    return fromEnv.replace(/\/$/, "");
  }

  const { protocol, hostname, port } = window.location;
  if (port === "5173" || port === "5174") {
    return "http://127.0.0.1:5000";
  }

  return "";
}

export default function App() {
  const [user, setUser] = useState(null);
  const [authStatus, setAuthStatus] = useState("loading");
  const [authError, setAuthError] = useState(null);
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem("flx-theme") !== "light");

  const [query, setQuery] = useState(() => readQueryState());
  const [rows, setRows] = useState([]);
  const [meta, setMeta] = useState({ page: 1, per_page: 25, total: 0 });
  const [loadingOrders, setLoadingOrders] = useState(false);
  const [ordersError, setOrdersError] = useState(null);
  const [ordersVisible, setOrdersVisible] = useState(true);
  const [actionBusyId, setActionBusyId] = useState(null);
  const [hoverOrderId, setHoverOrderId] = useState(null);
  const [pinnedOrderId, setPinnedOrderId] = useState(null);

  const backendBase = useMemo(() => inferBackendBase(), []);

  useEffect(() => {
    const initial = readQueryState();
    setQuery(initial);
    writeQueryState(initial, true);

    const onPopState = () => setQuery(readQueryState());
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  useEffect(() => {
    localStorage.setItem("flx-theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  useEffect(() => {
    const controller = new AbortController();

    async function bootstrap() {
      setAuthStatus("loading");
      setAuthError(null);
      try {
        const me = await getAuthMe(controller.signal);
        setUser(me);
        setAuthStatus("ok");
      } catch (error) {
        if (error?.status === 401) {
          setAuthStatus("unauthorized");
          return;
        }
        setAuthError(error);
        setAuthStatus("error");
      }
    }

    bootstrap();
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (authStatus !== "ok") return;

    const controller = new AbortController();

    async function loadOrders() {
      setLoadingOrders(true);
      setOrdersError(null);
      try {
        const result = await getOrders(query, controller.signal);
        setRows(result.data);
        setMeta(result.meta || {});
      } catch (error) {
        if (controller.signal.aborted) return;
        if (error?.status === 401) {
          setAuthStatus("unauthorized");
          return;
        }
        setOrdersError(error);
      } finally {
        if (!controller.signal.aborted) {
          setLoadingOrders(false);
        }
      }
    }

    loadOrders();
    return () => controller.abort();
  }, [query, authStatus]);

  function applyQuery(next, replace = false) {
    writeQueryState(next, replace);
    setQuery(next);
  }

  function patchQuery(patch) {
    const next = withPageReset(query, patch);
    applyQuery(next);
  }

  function setPage(nextPage) {
    const next = { ...query, page: String(nextPage) };
    applyQuery(next);
  }

  function resetFilters() {
    applyQuery(
      { ...DEFAULT_QUERY, page: "1", per_page: query.per_page || DEFAULT_QUERY.per_page }
    );
  }

  async function refreshOrders(currentQuery) {
    setLoadingOrders(true);
    setOrdersError(null);
    try {
      const result = await getOrders(currentQuery);
      setRows(result.data);
      setMeta(result.meta || {});
    } catch (error) {
      if (error?.status === 401) {
        setAuthStatus("unauthorized");
        return;
      }
      setOrdersError(error);
    } finally {
      setLoadingOrders(false);
    }
  }

  async function handleMoveWarehouse(orderId) {
    setActionBusyId(orderId);
    try {
      await postLegacyAction(`/stock_order/${orderId}`);
      await refreshOrders(query);
    } catch (error) {
      setOrdersError(error);
    } finally {
      setActionBusyId(null);
    }
  }

  async function handleDeliverDirect(orderId) {
    setActionBusyId(orderId);
    try {
      await postLegacyAction(`/deliver_direct/${orderId}`);
      await refreshOrders(query);
    } catch (error) {
      setOrdersError(error);
    } finally {
      setActionBusyId(null);
    }
  }

  useEffect(() => {
    if (!rows.length) {
      setHoverOrderId(null);
      setPinnedOrderId(null);
      return;
    }
    const rowIds = new Set(rows.map((row) => row.id));
    if (hoverOrderId !== null && !rowIds.has(hoverOrderId)) {
      setHoverOrderId(null);
    }
    if (pinnedOrderId !== null && !rowIds.has(pinnedOrderId)) {
      setPinnedOrderId(null);
    }
  }, [rows, hoverOrderId, pinnedOrderId]);

  const highlightedOrderId = pinnedOrderId ?? hoverOrderId;

  const effectiveMeta = useMemo(
    () => ({
      page: meta.page || Number(query.page) || Number(DEFAULT_QUERY.page),
      per_page: meta.per_page || Number(query.per_page) || Number(DEFAULT_QUERY.per_page),
      total: meta.total || 0,
    }),
    [meta, query.page, query.per_page]
  );

  const counters = useMemo(() => {
    const byStatus = { incoming: 0, stocked: 0, delivered: 0 };

    for (const row of rows) {
      const s = normalizeStatus(row.transit_status);
      if (s.includes("arrived")) {
        byStatus.stocked += 1;
      } else if (s.includes("delivered")) {
        byStatus.delivered += 1;
      } else {
        byStatus.incoming += 1;
      }
    }

    return byStatus;
  }, [rows]);

  if (authStatus === "loading") return <LoadingSkeleton />;
  if (authStatus === "unauthorized") return <Unauthorized />;
  if (authStatus === "error") return <ErrorBanner error={authError} />;

  return (
    <AppShell
      user={user}
      darkMode={darkMode}
      onToggleDark={() => setDarkMode((v) => !v)}
      backendBase={backendBase}
    >
      <section className="kpi-grid">
        <article className="kpi-card">
          <p>Transit / Incoming Orders</p>
          <strong>{counters.incoming}</strong>
        </article>
        <article className="kpi-card">
          <p>Stocked Items / In Stock</p>
          <strong>{counters.stocked}</strong>
        </article>
        <article className="kpi-card">
          <p>Completed Deliveries</p>
          <strong>{counters.delivered}</strong>
        </article>
      </section>

      <section className="orders-section-wrap">
        <div className="orders-headline">
          <h2>Your Orders</h2>
          <button
            type="button"
            className="toggle-orders"
            onClick={() => setOrdersVisible((v) => !v)}
          >
            {ordersVisible ? "Hide Orders" : "Show Orders"}
          </button>
        </div>

        {ordersVisible ? (
          <>
            <OrdersToolbar query={query} onPatch={patchQuery} onReset={resetFilters} />
            <ErrorBanner error={ordersError} />
            {loadingOrders ? <LoadingSkeleton /> : null}
            {!loadingOrders && rows.length === 0 ? <EmptyState /> : null}
            {!loadingOrders && rows.length > 0 ? (
              <>
                <OrdersTable
                  rows={rows}
                  role={user?.role}
                  busyId={actionBusyId}
                  onMoveWarehouse={handleMoveWarehouse}
                  onDeliverDirect={handleDeliverDirect}
                  highlightedId={highlightedOrderId}
                  pinnedId={pinnedOrderId}
                  onRowHover={setHoverOrderId}
                  onRowLeave={() => setHoverOrderId(null)}
                  onRowPin={(id) => setPinnedOrderId((prev) => (prev === id ? null : id))}
                />
                <Pagination
                  page={effectiveMeta.page}
                  perPage={effectiveMeta.per_page}
                  total={effectiveMeta.total}
                  onPageChange={setPage}
                />
                <TimelineGantt
                  rows={rows}
                  year={query["filter[year]"]}
                  onYearChange={(nextYear) => patchQuery({ "filter[year]": String(nextYear) })}
                  highlightedId={highlightedOrderId}
                  pinnedId={pinnedOrderId}
                  onItemHover={setHoverOrderId}
                  onItemLeave={() => setHoverOrderId(null)}
                  onItemPin={(id) => setPinnedOrderId((prev) => (prev === id ? null : id))}
                />
              </>
            ) : null}
          </>
        ) : null}
      </section>
    </AppShell>
  );
}
