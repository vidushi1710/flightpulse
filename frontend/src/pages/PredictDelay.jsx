import { useState } from "react";
import { Link } from "react-router-dom";
import RiskBadge from "../components/RiskBadge";
import { predictFlight } from "../services/api";
import { routeDistance } from "../utils/geo";
import { show } from "../utils/format";

export default function PredictDelay({ form, onFormChange, onSaved }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const estimate = routeDistance(form.ORIGIN_AIRPORT, form.DESTINATION_AIRPORT);

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await predictFlight(form);
      setResult({
        ...data,
        origin: form.ORIGIN_AIRPORT,
        destination: form.DESTINATION_AIRPORT
      });

      onSaved({
        id: Date.now(),
        origin: form.ORIGIN_AIRPORT,
        destination: form.DESTINATION_AIRPORT,
        airline: form.AIRLINE,
        probability: data.delay_percentage,
        risk: data.risk_level,
        date: new Date().toLocaleString()
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <header className="page-head">
        <h1>Delay prediction</h1>
        <p>
          Enter a flight’s details to estimate its chance of delay. You can also{" "}
          <Link className="inline-link" to="/">pick the route on the map</Link>.
        </p>
      </header>

      <div className="predict-grid">
        <form className="card" onSubmit={submit}>
          <div className="form-grid">
            <div className="field">
              <label htmlFor="origin">Origin airport</label>
              <input id="origin" required maxLength={4} value={form.ORIGIN_AIRPORT}
                onChange={e => onFormChange("ORIGIN_AIRPORT", e.target.value.toUpperCase())} />
            </div>

            <div className="field">
              <label htmlFor="destination">Destination airport</label>
              <input id="destination" required maxLength={4} value={form.DESTINATION_AIRPORT}
                onChange={e => onFormChange("DESTINATION_AIRPORT", e.target.value.toUpperCase())} />
            </div>

            <div className="field">
              <label htmlFor="airline">Airline code</label>
              <input id="airline" required maxLength={3} value={form.AIRLINE}
                onChange={e => onFormChange("AIRLINE", e.target.value.toUpperCase())} />
            </div>

            <div className="field">
              <label htmlFor="distance">Distance (miles)</label>
              <input id="distance" required type="number" min="1" value={form.DISTANCE}
                onChange={e => onFormChange("DISTANCE", e.target.value)} />
              {estimate && Number(form.DISTANCE) !== estimate && (
                <button type="button" className="link-action field-hint"
                  onClick={() => onFormChange("DISTANCE", estimate)}>
                  Use estimated {estimate} mi
                </button>
              )}
            </div>

            <div className="field">
              <label htmlFor="month">Month (1–12)</label>
              <input id="month" required type="number" min="1" max="12" value={form.MONTH}
                onChange={e => onFormChange("MONTH", e.target.value)} />
            </div>

            <div className="field">
              <label htmlFor="dow">Day of week (1–7)</label>
              <input id="dow" required type="number" min="1" max="7" value={form.DAY_OF_WEEK}
                onChange={e => onFormChange("DAY_OF_WEEK", e.target.value)} />
            </div>

            <div className="field">
              <label htmlFor="dep">Departure hour (0–23)</label>
              <input id="dep" required type="number" min="0" max="23" value={form.DEP_HOUR}
                onChange={e => onFormChange("DEP_HOUR", e.target.value)} />
            </div>

            <div className="field">
              <label htmlFor="arr">Arrival hour (0–23)</label>
              <input id="arr" required type="number" min="0" max="23" value={form.ARR_HOUR}
                onChange={e => onFormChange("ARR_HOUR", e.target.value)} />
            </div>
          </div>

          <button className="button button-primary button-wide" disabled={loading}>
            {loading ? "Calculating…" : "Calculate delay probability"}
          </button>

          {error && <div className="message message-error" role="alert">{error}</div>}
        </form>

        <div className="card result-card" aria-live="polite">
          {result ? (
            <>
              <div className="result-route">{result.origin} to {result.destination}</div>

              <div className="result-number">
                {result.delay_percentage}
                <span>%</span>
              </div>

              <div className="result-meta">
                <RiskBadge level={result.risk_level} suffix=" risk" />
                <b>{result.prediction === 1 ? "Delay predicted" : "No delay predicted"}</b>
              </div>

              <dl className="result-facts">
                <div>
                  <dt>Classification threshold</dt>
                  <dd>{show(result.classification_threshold)}</dd>
                </div>
                <div>
                  <dt>Model training period</dt>
                  <dd>{show(result.model_period)}</dd>
                </div>
              </dl>

              <p className="disclaimer">
                Experimental estimate from historical data. It is not a live
                flight status or a forecast.
              </p>
            </>
          ) : (
            <div className="result-empty">
              <h3>Your estimate appears here</h3>
              <p>Fill in the flight details and choose Calculate delay probability.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}