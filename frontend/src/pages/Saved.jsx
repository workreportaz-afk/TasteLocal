import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client from "../api/client.js";

export default function Saved() {
  const [saved, setSaved] = useState([]);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    client
      .get("/saved/")
      .then(({ data }) => setSaved(data.results ?? data))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function handleRemove(savedId) {
    await client.delete(`/saved/${savedId}/`);
    setSaved((prev) => prev.filter((s) => s.id !== savedId));
  }

  return (
    <div>
      <h1>Saved Food Spots</h1>
      <p className="muted">Your favourite places — save spots while browsing, then build them into an itinerary.</p>

      {loading && <p>Loading...</p>}

      {!loading && saved.length === 0 && (
        <p>No saved spots yet. Tap the heart on any food experience. <Link to="/">Discover now →</Link></p>
      )}

      <div className="experience-grid">
        {saved.map((s) => (
          <div key={s.id} className="experience-card">
            {s.experience_detail.image && (
              <img src={s.experience_detail.image} alt={s.experience_detail.title} />
            )}
            <div className="experience-card-body">
              <Link to={`/experiences/${s.experience_detail.id}`}>
                <h3>{s.experience_detail.title}</h3>
              </Link>
              <p className="muted">{s.experience_detail.vendor_name}</p>
              <div className="experience-card-footer">
                <span>${s.experience_detail.price}</span>
                <button type="button" className="link-button" onClick={() => handleRemove(s.id)}>
                  Remove
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
