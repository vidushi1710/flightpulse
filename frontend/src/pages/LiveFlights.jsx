import { useState } from "react";
import { Search, RefreshCw, ChevronRight } from "lucide-react";
import { fetchLiveFlights } from "../services/api";
import { show } from "../utils/format";

export default function LiveFlights({ onSelectRoute }) {
  const [airport, setAirport] = useState("ATL");
  const [flights, setFlights] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");

    try {
      const records = await fetchLiveFlights(airport);
      setFlights(records);
      if (!records.length) setError("No flights were returned for this airport.");
    } catch (err) {
      setFlights([]);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function selectFlight(flight) {
    onSelectRoute(
      flight.ORIGIN_AIRPORT || flight.origin || airport,
      flight.DESTINATION_AIRPORT || flight.destination || ""
    );
  }

  return (
    <div className="page">
      <header className="page-head">
        <h1>Live flights</h1>
        <p>
          Flights returned by the connected aviation data service. Each search
          uses part of the monthly request limit, so results load only when you
          ask.
        </p>
      </header>

      <div className="search-row">
        <label className="visually-hidden" htmlFor="airport">Airport code</label>
        <input id="airport" value={airport} maxLength={4}
          onChange={e => setAirport(e.target.value.toUpperCase())}
          placeholder="Airport code, for example ATL" />

        <button className="button button-primary" onClick={load} disabled={loading}>
          {flights.length ? <RefreshCw size={15} aria-hidden="true" /> : <Search size={15} aria-hidden="true" />}
          {loading ? "Loading…" : flights.length ? "Refresh" : "Get flights"}
        </button>
      </div>

      {error && <div className="message message-error" role="alert">{error}</div>}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Airline / flight</th>
              <th>Origin</th>
              <th>Destination</th>
              <th>Status</th>
              <th><span className="visually-hidden">Action</span></th>
            </tr>
          </thead>
          <tbody>
            {flights.map((flight, index) => (
              <tr key={flight.id || index}>
                <td>{show(flight.AIRLINE || flight.airline || flight.flight_number)}</td>
                <td>{show(flight.ORIGIN_AIRPORT || flight.origin)}</td>
                <td>{show(flight.DESTINATION_AIRPORT || flight.destination)}</td>
                <td>{show(flight.status || flight.flight_status)}</td>
                <td className="cell-action">
                  <button className="link-action" onClick={() => selectFlight(flight)}>
                    Predict <ChevronRight size={14} aria-hidden="true" />
                  </button>
                </td>
              </tr>
            ))}

            {!flights.length && (
              <tr>
                <td colSpan="5" className="empty-state">
                  Search an airport to see available flights.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {flights.length > 0 && <p className="disclaimer">{flights.length} flights retrieved.</p>}
    </div>
  );
}