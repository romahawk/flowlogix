export const DEFAULT_QUERY = {
  page: "1",
  per_page: "25",
  sort: "eta:desc,etd:desc,order_date:desc,id:desc",
  "filter[transit_status]": "",
  "filter[year]": "",
  "filter[q]": "",
  "filter[buyer]": "",
  "filter[responsible]": "",
  "filter[transport]": "",
};

export function readQueryState() {
  const params = new URLSearchParams(window.location.search);
  const next = { ...DEFAULT_QUERY };

  for (const key of Object.keys(DEFAULT_QUERY)) {
    if (params.has(key)) {
      next[key] = params.get(key) ?? "";
    }
  }

  if (!next.page || Number(next.page) < 1) next.page = DEFAULT_QUERY.page;
  if (!next.per_page || Number(next.per_page) < 1) next.per_page = DEFAULT_QUERY.per_page;
  if (!next.sort) next.sort = DEFAULT_QUERY.sort;

  return next;
}

export function toSearchParams(query) {
  const params = new URLSearchParams();
  for (const [key, val] of Object.entries(query)) {
    if (val !== "" && val !== null && val !== undefined) {
      params.set(key, String(val));
    }
  }
  return params;
}

export function writeQueryState(query, replace = false) {
  const params = toSearchParams(query);
  const nextUrl = `${window.location.pathname}?${params.toString()}`;
  if (replace) {
    window.history.replaceState({}, "", nextUrl);
  } else {
    window.history.pushState({}, "", nextUrl);
  }
}

export function withPageReset(query, patch) {
  const merged = { ...query, ...patch, page: "1" };
  return merged;
}
