import { useEffect, useMemo, useState } from "react";
import AppShell from "./components/AppShell";
import EmptyState from "./components/EmptyState";
import ErrorBanner from "./components/ErrorBanner";
import LoadingSkeleton from "./components/LoadingSkeleton";
import OrdersTable from "./components/OrdersTable";
import OrdersToolbar from "./components/OrdersToolbar";
import Pagination from "./components/Pagination";
import { getAuthMe, getOrders } from "./lib/api";
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

export default function App() {
  const [user, setUser] = useState(null);
  const [authStatus, setAuthStatus] = useState("loading");
  const [authError, setAuthError] = useState(null);

  const [query, setQuery] = useState(() => readQueryState());
  const [rows, setRows] = useState([]);
  const [meta, setMeta] = useState({ page: 1, per_page: 25, total: 0 });
  const [loadingOrders, setLoadingOrders] = useState(false);
  const [ordersError, setOrdersError] = useState(null);

  useEffect(() => {
    writeQueryState(query, true);

    const onPopState = () => {
      setQuery(readQueryState());
    };

    window.addEventListener("popstate", onPopState);
    return () => {
      window.removeEventListener("popstate", onPopState);
    };
  }, []);

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
        setOrdersError(error);
      } finally {
        setLoadingOrders(false);
      }
    }

    loadOrders();
    writeQueryState(query, true);

    return () => controller.abort();
  }, [query, authStatus]);

  const canRenderOrders = authStatus === "ok";

  function patchQuery(patch) {
    const next = withPageReset(query, patch);
    setQuery(next);
  }

  function setPage(nextPage) {
    setQuery((prev) => ({ ...prev, page: nextPage }));
  }

  const effectiveMeta = useMemo(
    () => ({
      page: meta.page || Number(query.page) || Number(DEFAULT_QUERY.page),
      per_page: meta.per_page || Number(query.per_page) || Number(DEFAULT_QUERY.per_page),
      total: meta.total || 0,
    }),
    [meta, query.page, query.per_page]
  );

  if (authStatus === "loading") return <LoadingSkeleton />;
  if (authStatus === "unauthorized") return <Unauthorized />;
  if (authStatus === "error") return <ErrorBanner error={authError} />;

  return (
    <AppShell user={user}>
      <OrdersToolbar query={query} onPatch={patchQuery} />
      <ErrorBanner error={ordersError} />

      {canRenderOrders && loadingOrders ? <LoadingSkeleton /> : null}
      {canRenderOrders && !loadingOrders && rows.length === 0 ? <EmptyState /> : null}
      {canRenderOrders && !loadingOrders && rows.length > 0 ? <OrdersTable rows={rows} /> : null}

      <Pagination
        page={effectiveMeta.page}
        perPage={effectiveMeta.per_page}
        total={effectiveMeta.total}
        onPageChange={setPage}
      />
    </AppShell>
  );
}
