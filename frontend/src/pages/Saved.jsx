import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import client from "../api/client.js";

export default function Saved() {
  const { t, i18n } = useTranslation();
  const [saved, setSaved] = useState([]);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    client
      .get("/saved/")
      .then(({ data }) => setSaved(data.results ?? data))
      .finally(() => setLoading(false));
  }

  useEffect(load, [i18n.language]);

  async function handleRemove(savedId) {
    await client.delete(`/saved/${savedId}/`);
    setSaved((prev) => prev.filter((s) => s.id !== savedId));
  }

  return (
    <div>
      <h1>{t("saved.title")}</h1>
      <p className="muted">{t("saved.subtitle")}</p>

      {loading && <p>{t("common.loading")}</p>}

      {!loading && saved.length === 0 && (
        <p>{t("saved.empty")} <Link to="/">{t("common.discoverNow")}</Link></p>
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
                  {t("saved.remove")}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
