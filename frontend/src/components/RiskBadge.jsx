import { riskClass, show } from "../utils/format";

export default function RiskBadge({ level, suffix = "" }) {
  return (
    <span className={`risk-badge ${riskClass(level)}`}>
      {show(level)}
      {suffix}
    </span>
  );
}