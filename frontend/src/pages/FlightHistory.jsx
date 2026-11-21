import RiskBadge from "../components/RiskBadge";

export default function FlightHistory({ history, onClear }) {
  return (
    <div className="page">
      <header className="page-head">
        <h1>Recent predictions</h1>
        <p>Saved in this browser only. Clearing your browser data removes them.</p>
      </header>

      {history.length === 0 ? (
        <div className="empty-state empty-block">No predictions yet.</div>
      ) : (
        <div className="history-list">
          {history.map(item => (
            <div className="history-item" key={item.id}>
              <div>
                <strong>{item.origin} to {item.destination}</strong>
                <small>{item.airline} · {item.date}</small>
              </div>

              <div className="history-result">
                <strong>{item.probability}%</strong>
                <RiskBadge level={item.risk} />
              </div>
            </div>
          ))}
        </div>
      )}

      {history.length > 0 && (
        <button
          className="link-action clear-button"
          onClick={() => {
            if (window.confirm("Clear all prediction history?")) onClear();
          }}
        >
          Clear history
        </button>
      )}
    </div>
  );
}