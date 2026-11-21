// Use the risk level returned by the backend instead of guessing thresholds here.
export function riskClass(level) {
  const key = String(level || "").toLowerCase();
  return ["low", "medium", "high"].includes(key) ? key : "unknown";
}

// Never invent data: anything missing is shown as "Unavailable".
export function show(value) {
  return value === undefined || value === null || value === ""
    ? "Unavailable"
    : value;
}