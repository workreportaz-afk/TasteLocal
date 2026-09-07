import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import client from "../api/client.js";

export default function PlanMyTrip() {
  const { t } = useTranslation();
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
      <h1>{t("trip.title")}</h1>
      <p className="muted">{t("trip.subtitle")}</p>

      {loading && <p>{t("common.loading")}</p>}

      {!loading && stops.length === 0 && (
        <p>{t("trip.empty")} <Link to="/">{t("common.discoverNow")}</Link></p>
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
                {t("trip.date")}
                <input
                  type="date"
                  value={stop.planned_date || ""}
                  onChange={(e) => handleDateChange(stop.id, e.target.value)}
                />
              </label>
              <button type="button" className="link-button" onClick={() => handleRemove(stop.id)}>
                {t("trip.remove")}
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
