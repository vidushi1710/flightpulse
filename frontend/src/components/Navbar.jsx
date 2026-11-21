import { NavLink } from "react-router-dom";
import { Plane } from "lucide-react";

const STATUS_LABELS = {
  checking: "Checking connection",
  online: "Connected",
  offline: "Backend offline"
};

const links = [
  { to: "/", label: "Map", end: true },
  { to: "/predict", label: "Predict" },
  { to: "/flights", label: "Flights" },
  { to: "/history", label: "History" }
];

export default function Navbar({
  dark,
  apiStatus,
  onRecheck,
  planeCursor,
  onTogglePlaneCursor
}) {
  return (
    <nav className={`navbar ${dark ? "navbar-dark" : ""}`} aria-label="Main">
      <NavLink className="brand" to="/">
        <Plane size={18} aria-hidden="true" />
        FlightPulse
      </NavLink>

      <div className="nav-links">
        {links.map(link => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.end}
            className={({ isActive }) => (isActive ? "active" : undefined)}
          >
            {link.label}
          </NavLink>
        ))}
      </div>

      <div className="nav-actions">
        <button
          type="button"
          className="toggle-pill"
          aria-pressed={planeCursor}
          onClick={onTogglePlaneCursor}
          title="Switch the airplane cursor on or off"
        >
          Plane cursor {planeCursor ? "on" : "off"}
        </button>

        <button
          type="button"
          className={`status-pill ${apiStatus}`}
          onClick={onRecheck}
          title="Check the backend connection again"
        >
          <span className="status-dot" aria-hidden="true" />
          {STATUS_LABELS[apiStatus]}
        </button>
      </div>
    </nav>
  );
}