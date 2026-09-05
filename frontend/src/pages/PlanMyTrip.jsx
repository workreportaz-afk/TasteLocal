import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client from "../api/client.js";

export default function PlanMyTrip() {
  const [stops, setStops] = useState([]);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    client
      .get("/itinerary/")
      .then(({ data }) => setStops(data.results ?? data))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function handleRemove(stopId) {
    await client.delete(`/itinerary/${stopId}/`);
    setStops((prev) => prev.filter((s) => s.id !== stopId));
  }

  async function handleDateChange(stopId, planned_date) {
    await client.patch(`/itinerary/${stopId}/`, { planned_date: planned_date || null });
    setStops((prev) => prev.map((s) => (s.id === stopId ? { ...s, planned_date } : s)));
  }

  return (
    <div>
      <h1>Plan My Trip</h1>
      <p className="muted">Your foodie itinerary — add stops from any experience page, then set a date for each.</p>

      {loading && <p>Loading...</p>}

      {!loading && stops.length === 0 && (
        <p>No trip stops yet. Add an experience to your trip from its page. <Link to="/">Discover now →</Link></p>
      )}

      <ul className="itinerary-list">
        {stops.map((stop) => (
          <li key={stop.id} className="itinerary-stop">
            <div>
              <Link to={`/experiences/${stop.experience_detail.id}`}>
                <strong>{stop.experience_detail.title}</strong>
              </Link>
              <p className="muted">{stop.experience_detail.vendor_name} · ${stop.experience_detail.price}</p>
              {stop.notes && <p>{stop.notes}</p>}
            </div>
            <div className="itinerary-stop-actions">
              <label>
                Date
                <input
                  type="date"
                  value={stop.planned_date || ""}
                  onChange={(e) => handleDateChange(stop.id, e.target.value)}
                />
              </label>
              <button type="button" className="link-button" onClick={() => handleRemove(stop.id)}>
                Remove
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
