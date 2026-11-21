// A fixed list of major US airports used for the map.
// Coordinates are public geographic facts. This list is NOT the set of airports
// the ML model supports; that needs a backend endpoint.
export const AIRPORTS = [
  { code: "ATL", name: "Hartsfield–Jackson Atlanta", lat: 33.6407, lng: -84.4277 },
  { code: "BOS", name: "Boston Logan", lat: 42.3656, lng: -71.0096 },
  { code: "CLT", name: "Charlotte Douglas", lat: 35.2144, lng: -80.9473 },
  { code: "DEN", name: "Denver International", lat: 39.8561, lng: -104.6737 },
  { code: "DFW", name: "Dallas/Fort Worth", lat: 32.8998, lng: -97.0403 },
  { code: "DTW", name: "Detroit Metropolitan", lat: 42.2162, lng: -83.3554 },
  { code: "EWR", name: "Newark Liberty", lat: 40.6895, lng: -74.1745 },
  { code: "IAH", name: "Houston George Bush", lat: 29.9902, lng: -95.3368 },
  { code: "JFK", name: "New York John F. Kennedy", lat: 40.6413, lng: -73.7781 },
  { code: "LAS", name: "Las Vegas Harry Reid", lat: 36.084, lng: -115.1537 },
  { code: "LAX", name: "Los Angeles International", lat: 33.9416, lng: -118.4085 },
  { code: "MCO", name: "Orlando International", lat: 28.4312, lng: -81.3081 },
  { code: "MIA", name: "Miami International", lat: 25.7959, lng: -80.287 },
  { code: "MSP", name: "Minneapolis–St. Paul", lat: 44.8848, lng: -93.2223 },
  { code: "ORD", name: "Chicago O’Hare", lat: 41.9742, lng: -87.9073 },
  { code: "PHX", name: "Phoenix Sky Harbor", lat: 33.4342, lng: -112.0116 },
  { code: "SEA", name: "Seattle–Tacoma", lat: 47.4502, lng: -122.3088 },
  { code: "SFO", name: "San Francisco International", lat: 37.6213, lng: -122.379 }
];

export const AIRPORT_BY_CODE = Object.fromEntries(
  AIRPORTS.map(airport => [airport.code, airport])
);

const toRad = degrees => (degrees * Math.PI) / 180;

// Great-circle distance in statute miles (haversine formula).
export function distanceMiles(a, b) {
  const R = 3958.8;
  const dLat = toRad(b.lat - a.lat);
  const dLng = toRad(b.lng - a.lng);
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(a.lat)) * Math.cos(toRad(b.lat)) * Math.sin(dLng / 2) ** 2;
  return Math.round(2 * R * Math.asin(Math.sqrt(h)));
}

// Estimated distance between two airport codes, or null if either is unknown.
export function routeDistance(originCode, destinationCode) {
  const a = AIRPORT_BY_CODE[originCode];
  const b = AIRPORT_BY_CODE[destinationCode];
  if (!a || !b || a.code === b.code) return null;
  return distanceMiles(a, b);
}

// A gentle curve between two points, drawn as a quadratic Bézier.
// Fine for the continental US. It does not handle routes crossing the antimeridian.
export function arcPoints(from, to, steps = 80) {
  const [lat1, lng1] = from;
  const [lat2, lng2] = to;
  const dLat = lat2 - lat1;
  const dLng = lng2 - lng1;

  let offsetLat = -dLng * 0.18;
  let offsetLng = dLat * 0.18;
  if (offsetLat < 0) {
    offsetLat = -offsetLat;
    offsetLng = -offsetLng;
  }

  const cLat = (lat1 + lat2) / 2 + offsetLat;
  const cLng = (lng1 + lng2) / 2 + offsetLng;

  const points = [];
  for (let i = 0; i <= steps; i += 1) {
    const t = i / steps;
    const u = 1 - t;
    points.push([
      u * u * lat1 + 2 * u * t * cLat + t * t * lat2,
      u * u * lng1 + 2 * u * t * cLng + t * t * lng2
    ]);
  }
  return points;
}