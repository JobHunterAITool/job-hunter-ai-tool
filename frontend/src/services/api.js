const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").trim();

function buildUrl(path) {
  if (!API_BASE_URL) {
    return path;
  }

  const base = API_BASE_URL.endsWith("/") ? API_BASE_URL.slice(0, -1) : API_BASE_URL;
  return `${base}${path}`;
}

export async function searchJobs(payload) {
  const response = await fetch(buildUrl("/search"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Search request failed (${response.status}): ${errorBody}`);
  }

  return response.json();
}
