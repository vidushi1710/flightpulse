import { PLANE_PATHS } from "../utils/plane";

export default function PlaneIcon({ size = 24, className }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      className={className}
      aria-hidden="true"
      focusable="false"
    >
      {PLANE_PATHS.map(path => (
        <path key={path} d={path} />
      ))}
    </svg>
  );
}