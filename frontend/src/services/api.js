const API = "http://localhost:8080";

const OFFLINE_MESSAGE =
  "Cannot reach the backend on port 8080. Start Spring Boot and try again.";

// fetch() throws a TypeError when the server is unreachable.
async function send(path, options) {
  try {
    return await fetch(`${API}${path}`, options);
  } catch {
    throw new Error(OFFLINE_MESSAGE);
  }
}

export async function checkHealth() {
  try {
    const response = await fetch(`${API}/api/health`);
    return response.ok;
  } catch {
    return false;
  }
}

export async function predictFlight(form) {
  const response = await send("/api/flights/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ...form,
      MONTH: Number(form.MONTH),
      DAY_OF_WEEK: Number(form.DAY_OF_WEEK),
      DEP_HOUR: Number(form.DEP_HOUR),
      ARR_HOUR: Number(form.ARR_HOUR),
      DISTANCE: Number(form.DISTANCE)
    })
  });

  if (!response.ok) {
    throw new Error(
      "The prediction service returned an error. Check that the Spring Boot and Python services are running."
    );
  }

  return response.json();
}

export async function fetchLiveFlights(airport, limit = 20) {
  const response = await send(
    `/api/flights/live?airport=${encodeURIComponent(airport)}&limit=${limit}`
  );

  if (!response.ok) {
    throw new Error("Unable to retrieve flights from the backend.");
  }

  const data = await response.json();
  return Array.isArray(data) ? data : data.flights || data.data || [];
}