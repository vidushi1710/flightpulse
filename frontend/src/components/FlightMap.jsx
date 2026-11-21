import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { AIRPORTS, AIRPORT_BY_CODE, arcPoints } from "../utils/geo";
import { PLANE_PATHS } from "../utils/plane";

const PLANE_SVG = `<svg viewBox="0 0 24 24" width="30" height="30" aria-hidden="true" focusable="false">${PLANE_PATHS.map(
  path => `<path d="${path}" />`
).join("")}</svg>`;

// OpenStreetMap's public tiles need no API key. They are light-coloured, so the
// stylesheet darkens them with a CSS filter. Fine for development and light use;
// a production site should use a tile provider with its own key.
const TILES = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
const ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

export default function FlightMap({ origin, destination, onSelect }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const markersRef = useRef(null);
  const routeRef = useRef(null);
  const onSelectRef = useRef(onSelect);

  useEffect(() => {
    onSelectRef.current = onSelect;
  });

  // Create the map once.
  useEffect(() => {
    const map = L.map(containerRef.current, {
      zoomControl: false,
      worldCopyJump: true,
      minZoom: 2
    });

    L.control.zoom({ position: "bottomright" }).addTo(map);
    L.tileLayer(TILES, {
      attribution: ATTRIBUTION,
      maxZoom: 19
    }).addTo(map);

    // Start with a fixed view, then fit to the airports once the container has a
    // real size. Fitting a zero-size map throws an error and blanks the page.
    map.setView([39, -96], 4);
    const startFrame = requestAnimationFrame(() => {
      map.invalidateSize();
      const size = map.getSize();
      if (size.x > 0 && size.y > 0) {
        map.fitBounds(L.latLngBounds(AIRPORTS.map(a => [a.lat, a.lng])), {
          padding: [60, 60]
        });
      }
    });

    markersRef.current = L.layerGroup().addTo(map);
    routeRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;

    const observer = new ResizeObserver(() => map.invalidateSize());
    observer.observe(containerRef.current);

    return () => {
      cancelAnimationFrame(startFrame);
      observer.disconnect();
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Airport markers. Selected airports get a highlighted style.
  useEffect(() => {
    const group = markersRef.current;
    if (!group) return;

    group.clearLayers();

    AIRPORTS.forEach(airport => {
      const role =
        airport.code === origin
          ? "origin"
          : airport.code === destination
            ? "destination"
            : "";

      const icon = L.divIcon({
        className: `airport-pin ${role} ${airport.code === "EWR" ? "label-left" : ""}`,
        html: `<span class="pin-dot"></span><span class="pin-label">${airport.code}</span>`,
        iconSize: [12, 12],
        iconAnchor: [6, 6]
      });

      L.marker([airport.lat, airport.lng], {
        icon,
        title: `${airport.name} (${airport.code})`,
        riseOnHover: true,
        keyboard: true
      })
        .on("click", () => onSelectRef.current(airport.code))
        .addTo(group);
    });
  }, [origin, destination]);

  // Route arc and the gliding plane preview.
  useEffect(() => {
    const map = mapRef.current;
    const layer = routeRef.current;
    if (!map || !layer) return undefined;

    layer.clearLayers();

    const from = AIRPORT_BY_CODE[origin];
    const to = AIRPORT_BY_CODE[destination];
    if (!from || !to) return undefined;

    const points = arcPoints([from.lat, from.lng], [to.lat, to.lng], 80);

    L.polyline(points, {
      color: "#D62839",
      weight: 2.5,
      opacity: 0.9,
      dashArray: "6 8",
      interactive: false
    }).addTo(layer);

    const size = map.getSize();
    if (size.x > 0 && size.y > 0) {
      map.fitBounds(L.latLngBounds(points), {
        paddingTopLeft: [window.innerWidth > 900 ? 380 : 40, 150],
        paddingBottomRight: [60, 70],
        maxZoom: 6
      });
    }

    const plane = L.marker(points[0], {
      icon: L.divIcon({
        className: "route-plane",
        html: `<div class="route-plane-inner">${PLANE_SVG}</div>`,
        iconSize: [30, 30],
        iconAnchor: [15, 15]
      }),
      interactive: false,
      keyboard: false,
      zIndexOffset: 1000
    }).addTo(layer);

    function placeAt(progress) {
      const position = progress * (points.length - 1);
      const index = Math.min(Math.floor(position), points.length - 2);
      const fraction = position - index;
      const p0 = points[index];
      const p1 = points[index + 1];

      plane.setLatLng([
        p0[0] + (p1[0] - p0[0]) * fraction,
        p0[1] + (p1[1] - p0[1]) * fraction
      ]);

      const s0 = map.latLngToContainerPoint(p0);
      const s1 = map.latLngToContainerPoint(p1);
      const angle = Math.atan2(s1.y - s0.y, s1.x - s0.x);
      const inner = plane.getElement()?.querySelector(".route-plane-inner");
      if (inner) inner.style.transform = `rotate(${angle}rad)`;
    }

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      placeAt(0.5);
      return () => layer.clearLayers();
    }

    const duration = 6000;
    let start = null;
    let frame = 0;

    function tick(now) {
      if (start === null) start = now;
      const t = ((now - start) % duration) / duration;
      placeAt(t * t * (3 - 2 * t));
      frame = requestAnimationFrame(tick);
    }

    frame = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(frame);
      layer.clearLayers();
    };
  }, [origin, destination]);

  return (
    <div
      ref={containerRef}
      className="map-canvas"
      role="application"
      aria-label="Interactive airport map"
    />
  );
}