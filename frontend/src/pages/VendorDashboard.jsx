import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import client from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";

const emptyForm = {
  title: "", description: "", category: "street_food",
  price: "", duration_minutes: 60, max_participants: 10, address: "",
  latitude: "", longitude: "",
};

export default function VendorDashboard() {
  const { t } = useTranslation();
  const { vendorId, vendorIsApproved } = useAuth();
  const [experiences, setExperiences] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [message, setMessage] = useState("");
  const [geocoding, setGeocoding] = useState(false);

  function loadMine() {
    if (!vendorId) return;
    client.get("/experiences/", { params: { vendor: vendorId } }).then(({ data }) => {
      setExperiences(data.results ?? data);
    });
  }

  useEffect(loadMine, [vendorId]);

  function update(field) {
    return (e) => setForm({ ...form, [field]: e.target.value });
  }

  function handleImageChange(e) {
    const file = e.target.files[0];
    if (!file) {
      setImageFile(null);
      setImagePreview(null);
      return;
    }
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file)); // local preview only, not uploaded until submit
  }

  // Free geocoding via OpenStreetMap's Nominatim -- no API key required.
  // Nominatim's usage policy asks for light, non-bulk use, which fits a
  // one-off "look up this address" click.
  async function handleGeocode() {
    if (!form.address) {
      setMessage(t("vendor.enterAddressFirst"));
      return;
    }
    setGeocoding(true);
    setMessage("");
    try {
      const params = new URLSearchParams({
        format: "json",
        q: form.address,
        countrycodes: "sg",
        limit: "1",
      });
      const res = await fetch(`https://nominatim.openstreetmap.org/search?${params}`);
      const results = await res.json();
      if (results.length === 0) {
        setMessage(t("vendor.addressNotFound"));
        return;
      }
      setForm((f) => ({ ...f, latitude: results[0].lat, longitude: results[0].lon }));
      setMessage(t("vendor.coordinatesFound"));
    } catch {
      setMessage(t("vendor.geocodeFailed"));
    } finally {
      setGeocoding(false);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setMessage("");
    try {
      // Only switch to multipart/form-data when there's actually a file to
      // send -- plain JSON is simpler and works fine for text-only listings.
      if (imageFile) {
        const formData = new FormData();
        Object.entries(form).forEach(([key, value]) => {
          if (value !== "" && value !== null) formData.append(key, value);
        });
        formData.append("image", imageFile);
        await client.post("/experiences/", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
      } else {
        await client.post("/experiences/", form);
      }
      setForm(emptyForm);
      setImageFile(null);
      setImagePreview(null);
      setMessage(t("vendor.experienceCreated"));
      loadMine();
    } catch (err) {
      setMessage(t("vendor.saveFailed"));
    }
  }

  return (
    <div className="vendor-dashboard">
      <h1>{t("vendor.title")}</h1>

      {vendorIsApproved === false && (
        <p className="approval-banner">{t("vendor.pendingApproval")}</p>
      )}

      <form onSubmit={handleSubmit} className="experience-form">
        <h2>{t("vendor.listNew")}</h2>
        <label>{t("vendor.titleLabel")} <input value={form.title} onChange={update("title")} required /></label>
        <label>{t("vendor.description")} <textarea value={form.description} onChange={update("description")} required /></label>
        <label>
          {t("vendor.category")}
          <select value={form.category} onChange={update("category")}>
            <option value="street_food">{t("category.street_food")}</option>
            <option value="fine_dining">{t("category.fine_dining")}</option>
            <option value="cooking_class">{t("category.cooking_class")}</option>
            <option value="market_tour">{t("category.market_tour")}</option>
            <option value="tasting">{t("category.tasting")}</option>
          </select>
        </label>
        <label>{t("vendor.priceLabel")} <input type="number" step="0.01" value={form.price} onChange={update("price")} required /></label>
        <label>{t("vendor.durationLabel")} <input type="number" value={form.duration_minutes} onChange={update("duration_minutes")} /></label>
        <label>{t("vendor.maxParticipantsLabel")} <input type="number" value={form.max_participants} onChange={update("max_participants")} /></label>
        <label>{t("vendor.address")} <input value={form.address} onChange={update("address")} /></label>
        <button type="button" onClick={handleGeocode} disabled={geocoding}>
          {geocoding ? t("vendor.lookingUp") : t("vendor.findCoordinates")}
        </button>
        {form.latitude && form.longitude && (
          <p className="muted">{t("vendor.coordinatesLabel", { lat: form.latitude, lng: form.longitude })}</p>
        )}
        <label>
          {t("vendor.photo")}
          <input type="file" accept="image/*" onChange={handleImageChange} />
        </label>
        {imagePreview && <img src={imagePreview} alt="Preview" className="image-preview" />}
        <button type="submit">{t("vendor.publish")}</button>
        {message && <p className="message">{message}</p>}
      </form>

      <h2>{t("vendor.yourListings")}</h2>
      <ul className="vendor-list">
        {experiences.map((exp) => (
          <li key={exp.id} className="vendor-list-item">
            {exp.image && <img src={exp.image} alt={exp.title} className="vendor-list-thumb" />}
            <span>{exp.title} — ${exp.price} ({t(`category.${exp.category}`)})</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
