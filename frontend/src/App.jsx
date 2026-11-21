import { useCallback, useEffect, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import Navbar from "./components/Navbar";
import PlaneCursor from "./components/PlaneCursor";
import Home from "./pages/Home";
import PredictDelay from "./pages/PredictDelay";
import LiveFlights from "./pages/LiveFlights";
import FlightHistory from "./pages/FlightHistory";
import { checkHealth } from "./services/api";
import { routeDistance } from "./utils/geo";
import "./App.css";

const HISTORY_KEY = "flightpulse-history";
const CURSOR_KEY = "flightpulse-plane-cursor";

const initialForm = {
  MONTH: 11,
  DAY_OF_WEEK: 3,
  DEP_HOUR: 8,
  ARR_HOUR: 11,
  DISTANCE: routeDistance("ATL", "JFK") ?? 760,
  AIRLINE: "DL",
  ORIGIN_AIRPORT: "ATL",
  DESTINATION_AIRPORT: "JFK"
};

function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
  } catch {
    return [];
  }
}

function Shell() {
  const location = useLocation();
  const navigate = useNavigate();
  const isHome = location.pathname === "/";

  const [form, setForm] = useState(initialForm);
  const [route, setRoute] = useState({ origin: "", destination: "" });
  const [history, setHistory] = useState(loadHistory);
  const [apiStatus, setApiStatus] = useState("checking");
  const [planeCursor, setPlaneCursor] = useState(
    () => localStorage.getItem(CURSOR_KEY) !== "off"
  );

  const recheckApi = useCallback(async () => {
    setApiStatus("checking");
    setApiStatus((await checkHealth()) ? "online" : "offline");
  }, []);

  useEffect(() => {
    recheckApi();
  }, [recheckApi]);

  useEffect(() => {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
  }, [history]);

  useEffect(() => {
    localStorage.setItem(CURSOR_KEY, planeCursor ? "on" : "off");
  }, [planeCursor]);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [location.pathname]);

  function updateForm(key, value) {
    setForm(previous => ({ ...previous, [key]: value }));
  }

  // Put a route into the prediction form, filling in the estimated distance when known.
  function applyRoute(origin, destination) {
    const miles = routeDistance(origin, destination);
    setForm(previous => ({
      ...previous,
      ORIGIN_AIRPORT: origin,
      DESTINATION_AIRPORT: destination,
      ...(miles ? { DISTANCE: miles } : {})
    }));
  }

  function changeMapRoute(origin, destination) {
    setRoute({ origin, destination });
    if (origin && destination) applyRoute(origin, destination);
  }

  function selectRouteFromFlights(origin, destination) {
    applyRoute(origin, destination);
    navigate("/predict");
  }

  function addHistory(entry) {
    setHistory(previous => [entry, ...previous].slice(0, 30));
  }

  return (
    <div className="app">
      <Navbar
        dark={isHome}
        apiStatus={apiStatus}
        onRecheck={recheckApi}
        planeCursor={planeCursor}
        onTogglePlaneCursor={() => setPlaneCursor(value => !value)}
      />

      <main className={isHome ? "main-home" : "main-page"}>
        <Routes>
          <Route
            path="/"
            element={
              <Home
                origin={route.origin}
                destination={route.destination}
                onRouteChange={changeMapRoute}
              />
            }
          />
          <Route
            path="/predict"
            element={<PredictDelay form={form} onFormChange={updateForm} onSaved={addHistory} />}
          />
          <Route
            path="/flights"
            element={<LiveFlights onSelectRoute={selectRouteFromFlights} />}
          />
          <Route
            path="/history"
            element={<FlightHistory history={history} onClear={() => setHistory([])} />}
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      {!isHome && (
        <footer className="footer">
          <strong>FlightPulse</strong>
          <span>© 2026 FlightPulse · Academic project</span>
        </footer>
      )}

      <PlaneCursor enabled={planeCursor} />
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Shell />
    </BrowserRouter>
  );
}