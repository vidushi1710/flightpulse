import { useEffect, useRef } from "react";
import PlaneIcon from "./PlaneIcon";

const INTERACTIVE =
  "a, button, [role='button'], label, .leaflet-marker-icon, .leaflet-interactive";
const TEXT_FIELDS = "input, textarea, select";

function shortestAngle(from, to) {
  let diff = (to - from) % (Math.PI * 2);
  if (diff > Math.PI) diff -= Math.PI * 2;
  if (diff < -Math.PI) diff += Math.PI * 2;
  return diff;
}

// A small airplane that follows the mouse and turns toward its direction of travel.
// It only runs on devices with a mouse, and can be switched off from the navbar.
export default function PlaneCursor({ enabled }) {
  const outer = useRef(null);
  const inner = useRef(null);

  useEffect(() => {
    if (!enabled || !window.matchMedia("(pointer: fine)").matches) {
      return undefined;
    }

    const reduceMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;
    const el = outer.current;
    const body = inner.current;
    const root = document.documentElement;
    root.classList.add("plane-cursor-on");

    const target = { x: 0, y: 0 };
    const pos = { x: 0, y: 0 };
    let angle = -Math.PI / 4;
    let targetAngle = angle;
    let frame = 0;
    let seen = false;
    let overField = false;

    function setVisible(visible) {
      el.style.opacity = visible && !overField ? "1" : "0";
    }

    function onMove(event) {
      target.x = event.clientX;
      target.y = event.clientY;
      if (!seen) {
        pos.x = target.x;
        pos.y = target.y;
        seen = true;
      }
      setVisible(true);
    }

    function onOver(event) {
      const node = event.target;
      overField = Boolean(node.closest?.(TEXT_FIELDS));
      body.dataset.state = node.closest?.(INTERACTIVE) ? "link" : "";
      setVisible(true);
    }

    function onDown() {
      body.dataset.state = "press";
    }

    function onUp(event) {
      body.dataset.state = event.target.closest?.(INTERACTIVE) ? "link" : "";
    }

    function onLeave() {
      setVisible(false);
    }

    function tick() {
      const dx = target.x - pos.x;
      const dy = target.y - pos.y;

      if (!reduceMotion && Math.hypot(dx, dy) > 3) {
        targetAngle = Math.atan2(dy, dx);
      }

      const follow = reduceMotion ? 1 : 0.22;
      pos.x += dx * follow;
      pos.y += dy * follow;
      angle += shortestAngle(angle, targetAngle) * 0.14;

      el.style.transform = `translate3d(${pos.x}px, ${pos.y}px, 0) rotate(${angle}rad)`;
      frame = requestAnimationFrame(tick);
    }

    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseover", onOver);
    document.addEventListener("mousedown", onDown);
    document.addEventListener("mouseup", onUp);
    document.documentElement.addEventListener("mouseleave", onLeave);
    frame = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(frame);
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseover", onOver);
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("mouseup", onUp);
      document.documentElement.removeEventListener("mouseleave", onLeave);
      root.classList.remove("plane-cursor-on");
    };
  }, [enabled]);

  if (!enabled) return null;

  return (
    <div className="plane-cursor" ref={outer} aria-hidden="true">
      <div className="plane-cursor-inner" ref={inner}>
        <PlaneIcon size={30} />
      </div>
    </div>
  );
}