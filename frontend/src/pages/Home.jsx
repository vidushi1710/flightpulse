import { useNavigate } from "react-router-dom";
import FlightMap from "../components/FlightMap";
import { AIRPORTS, AIRPORT_BY_CODE, routeDistance } from "../utils/geo";

export default function Home({ origin, destination, onRouteChange }) {
  const navigate = useNavigate();
  const from = AIRPORT_BY_CODE[origin];
  const to = AIRPORT_BY_CODE[destination];
  const miles = routeDistance(origin, destination);

  // First click sets the origin, second sets the destination, third starts over.
  function handleSelect(code) {
    if (!origin || destination) onRouteChange(code, "");
    else if (code === origin) onRouteChange("", "");
    else onRouteChange(origin, code);
  }

  let hint = "Click an airport on the map, or use the menus below, to start a route.";
  if (origin && !destination) hint = "Now choose a destination airport.";

  return (
    <div className="home">
      <FlightMap origin={origin} destination={destination} onSelect={handleSelect} />

      <section className="map-panel" aria-label="Route planner">
        <h1>Where are you flying?</h1>
        <p>{hint}</p>

        <div className="panel-field">
          <label htmlFor="map-origin">From</label>
          <select
            id="map-origin"
            value={origin}
            onChange={e =>
              onRouteChange(e.target.value, e.target.value === destination ? "" : destination)
            }
          >
            <option value="">Select airport</option>
            {AIRPORTS.map(a => (
              <option key={a.code} value={a.code}>
                {a.code} · {a.name}
              </option>
            ))}
          </select>
        </div>

        <div className="panel-field">
          <label htmlFor="map-destination">To</label>
          <select
            id="map-destination"
            value={destination}
            onChange={e => onRouteChange(origin, e.target.value)}
          >
            <option value="">Select airport</option>
            {AIRPORTS.filter(a => a.code !== origin).map(a => (
              <option key={a.code} value={a.code}>
                {a.code} · {a.name}
              </option>
            ))}
          </select>
        </div>

        {from && to && (
          <div className="route-summary">
            <div className="route-codes">
              {from.code} <span aria-hidden="true">→</span> {to.code}
            </div>
            <div className="route-distance">
              About {miles} miles, estimated from airport coordinates
            </div>

            <div className="panel-actions">
              <button
                type="button"
                className="button button-primary"
                onClick={() => navigate("/predict")}
              >
                Check delay risk
              </button>
              <button
                type="button"
                className="link-action link-light"
                onClick={() => onRouteChange("", "")}
              >
                Clear
              </button>
            </div>
          </div>
        )}
      </section>

      <p className="map-note">
        Airports are a fixed sample list. The moving plane previews your chosen
        route; it is not a live flight.
      </p>
    </div>
  );
}