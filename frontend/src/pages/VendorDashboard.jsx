import { useEffect, useState } from "react";
import client from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";

const emptyForm = {
  title: "", description: "", category: "street_food",
  price: "", duration_minutes: 60, max_participants: 10, address: "",
  latitude: "", longitude: "",
};

export default function VendorDashboard() {
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
      setMessage("Enter an address first.");
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
        setMessage("Couldn't find that address. Try adding more detail (e.g. street + postal code).");
        return;
      }
      setForm((f) => ({ ...f, latitude: results[0].lat, longitude: results[0].lon }));
      setMessage("Coordinates found.");
    } catch {
      setMessage("Geocoding lookup failed. You can leave coordinates blank and add them later.");
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
      setMessage("Experience created.");
      loadMine();
    } catch (err) {
      setMessage("Could not save. Make sure you have a Vendor profile set up first.");
    }
  }

  return (
    <div className="vendor-dashboard">
      <h1>Vendor Dashboard</h1>

      {vendorIsApproved === false && (
        <p className="approval-banner">
          Your vendor account is pending admin approval. You can still create
          listings below — they just won't appear in public search results
          until an admin approves your account.
        </p>
      )}

      <form onSubmit={handleSubmit} className="experience-form">
        <h2>List a new experience</h2>
        <label>Title <input value={form.title} onChange={update("title")} required /></label>
        <label>Description <textarea value={form.description} onChange={update("description")} required /></label>
        <label>
          Category
          <select value={form.category} onChange={update("category")}>
            <option value="street_food">Street Food Tour</option>
            <option value="fine_dining">Fine Dining</option>
            <option value="cooking_class">Cooking Class</option>
            <option value="market_tour">Market Tour</option>
            <option value="tasting">Tasting Session</option>
          </select>
        </label>
        <label>Price (per person) <input type="number" step="0.01" value={form.price} onChange={update("price")} required /></label>
        <label>Duration (minutes) <input type="number" value={form.duration_minutes} onChange={update("duration_minutes")} /></label>
        <label>Max participants <input type="number" value={form.max_participants} onChange={update("max_participants")} /></label>
        <label>Address <input value={form.address} onChange={update("address")} /></label>
        <button type="button" onClick={handleGeocode} disabled={geocoding}>
          {geocoding ? "Looking up..." : "Find coordinates from address"}
        </button>
        {form.latitude && form.longitude && (
          <p className="muted">Coordinates: {form.latitude}, {form.longitude}</p>
        )}
        <label>
          Photo
          <input type="file" accept="image/*" onChange={handleImageChange} />
        </label>
        {imagePreview && <img src={imagePreview} alt="Preview" className="image-preview" />}
        <button type="submit">Publish experience</button>
        {message && <p className="message">{message}</p>}
      </form>

      <h2>Your listed experiences</h2>
      <ul className="vendor-list">
        {experiences.map((exp) => (
          <li key={exp.id} className="vendor-list-item">
            {exp.image && <img src={exp.image} alt={exp.title} className="vendor-list-thumb" />}
            <span>{exp.title} — ${exp.price} ({exp.category})</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
