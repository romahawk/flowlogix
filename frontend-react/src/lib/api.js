function parseErrorPayload(payload, fallbackMessage) {
  const apiError = payload?.error;
  if (!apiError) {
    return { message: fallbackMessage, details: [] };
  }
  return {
    message: apiError.message || fallbackMessage,
    details: Array.isArray(apiError.details) ? apiError.details : [],
    code: apiError.code || "UNKNOWN",
  };
}

export async function getAuthMe(signal) {
  const res = await fetch("/api/v1/auth/me", {
    method: "GET",
    credentials: "include",
    headers: { Accept: "application/json" },
    signal,
  });

  const payload = await res.json().catch(() => ({}));

  if (!res.ok) {
    const error = parseErrorPayload(payload, "Unable to load current user.");
    throw { status: res.status, ...error };
  }

  return payload.data;
}

export async function getOrders(query, signal) {
  const params = new URLSearchParams();
  for (const [key, val] of Object.entries(query)) {
    if (val !== "" && val !== null && val !== undefined) {
      params.set(key, String(val));
    }
  }

  const url = `/api/v1/orders?${params.toString()}`;
  const res = await fetch(url, {
    method: "GET",
    credentials: "include",
    headers: { Accept: "application/json" },
    signal,
  });

  const payload = await res.json().catch(() => ({}));

  if (!res.ok) {
    const error = parseErrorPayload(payload, "Unable to load orders.");
    throw { status: res.status, ...error };
  }

  return {
    data: Array.isArray(payload.data) ? payload.data : [],
    meta: payload.meta || {},
  };
}
