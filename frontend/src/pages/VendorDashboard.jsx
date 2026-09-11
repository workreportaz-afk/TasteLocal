import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import client from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";

const emptyForm = {
  title: "", description: "", category: "street_food",
  price: "", duration_minutes: 60, max_participants: 10, address: "",
  latitude: "", longitude: "",
};

const emptyStallForm = {
  business_name: "", description: "", cuisine_type: "", address: "", phone: "",
  opening_time: "", closing_time: "", hours_note: "",
};

// Vendor Dashboard shows "all of mine", not a paginated public feed, so we
// walk every page ourselves instead of showing Prev/Next controls here.
// Deliberately increments `page` through the existing `client` instance
// rather than following the absolute `next` URL DRF returns -- that URL's
// host is whatever Django saw the request come in on, which can differ
// from what the browser can actually reach (e.g. an internal Docker
// hostname), so re-requesting the same path with our own `page` param is
// the safer bet in both dev and prod.
async function fetchAllPages(path, params = {}) {
  let page = 1;
  let results = [];
  while (true) {
    const { data } = await client.get(path, { params: { ...params, page } });
    results = results.concat(data.results ?? data);
    if (!data.next) break;
    page += 1;
  }
  return results;
}

export default function VendorDashboard() {
  const { t } = useTranslation();
  const { vendorId, vendorIsApproved } = useAuth();
  const [experiences, setExperiences] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null); // experience id being edited, or null = "create new"
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [message, setMessage] = useState("");
  const [geocoding, setGeocoding] = useState(false);

  const [stallForm, setStallForm] = useState(emptyStallForm);
  const [stallMessage, setStallMessage] = useState("");

  const [bookings, setBookings] = useState([]);
  const [bookingMessage, setBookingMessage] = useState("");

  function loadMine() {
    if (!vendorId) return;
    // Previously only requested page 1, so a vendor with 13+ listings could
    // never see or edit anything past the 12th (PAGE_SIZE=12) -- e.g.
    // "Tian Tian Hainanese Chicken Rice Tasting" as item #13.
    fetchAllPages("/experiences/", { vendor: vendorId }).then(setExperiences);
  }

  function loadStall() {
    if (!vendorId) return;
    client.get("/vendors/me/").then(({ data }) => {
      setStallForm({
        business_name: data.business_name ?? "",
        description: data.description ?? "",
        cuisine_type: data.cuisine_type ?? "",
        address: data.address ?? "",
        phone: data.phone ?? "",
        opening_time: data.opening_time ?? "",
        closing_time: data.closing_time ?? "",
        hours_note: data.hours_note ?? "",
      });
    });
  }

  function loadBookings() {
    if (!vendorId) return;
    // Same pagination bug as loadMine() above -- a vendor with 13+ bookings
    // was silently missing anything past the first page, which is worse
    // here since it could hide a "pending" booking that still needs action.
    fetchAllPages("/vendor-bookings/").then(setBookings);
  }

  useEffect(loadMine, [vendorId]);
  useEffect(loadStall, [vendorId]);
  useEffect(loadBookings, [vendorId]);

  function update(field) {
    return (e) => setForm({ ...form, [field]: e.target.value });
  }

  function updateStall(field) {
    return (e) => setStallForm({ ...stallForm, [field]: e.target.value });
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

  function startEdit(exp) {
    setEditingId(exp.id);
    setForm({
      title: exp.title ?? "",
      description: exp.description ?? "",
      category: exp.category ?? "street_food",
      price: exp.price ?? "",
      duration_minutes: exp.duration_minutes ?? 60,
      max_participants: exp.max_participants ?? 10,
      address: exp.address ?? "",
      latitude: exp.latitude ?? "",
      longitude: exp.longitude ?? "",
    });
    setImageFile(null);
    setImagePreview(exp.image ?? null);
    setMessage("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function cancelEdit() {
    setEditingId(null);
    setForm(emptyForm);
    setImageFile(null);
    setImagePreview(null);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setMessage("");
    try {
      const isEditing = editingId !== null;
      // Only switch to multipart/form-data when there's actually a file to
      // send -- plain JSON is simpler and works fine for text-only listings.
      if (imageFile) {
        const formData = new FormData();
        Object.entries(form).forEach(([key, value]) => {
          if (value !== "" && value !== null) formData.append(key, value);
        });
        formData.append("image", imageFile);
        if (isEditing) {
          await client.patch(`/experiences/${editingId}/`, formData, {
            headers: { "Content-Type": "multipart/form-data" },
          });
        } else {
          await client.post("/experiences/", formData, {
            headers: { "Content-Type": "multipart/form-data" },
          });
        }
      } else if (isEditing) {
        await client.patch(`/experiences/${editingId}/`, form);
      } else {
        await client.post("/experiences/", form);
      }
      setMessage(isEditing ? t("vendor.experienceUpdated") : t("vendor.experienceCreated"));
      cancelEdit();
      loadMine();
    } catch (err) {
      setMessage(t("vendor.saveFailed"));
    }
  }

  async function handleStallSubmit(e) {
    e.preventDefault();
    setStallMessage("");
    try {
      await client.patch("/vendors/me/", stallForm);
      setStallMessage(t("vendor.stallUpdated"));
    } catch {
      setStallMessage(t("vendor.stallSaveFailed"));
    }
  }

  async function handleBookingAction(bookingId, status) {
    setBookingMessage("");
    try {
      await client.patch(`/vendor-bookings/${bookingId}/`, { status });
      loadBookings();
    } catch (err) {
      setBookingMessage(err.response?.data?.status?.[0] || t("vendor.bookingUpdateFailed"));
    }
  }

  return (
    <div className="vendor-dashboard">
      <h1>{t("vendor.title")}</h1>

      {vendorIsApproved === false && (
        <p className="approval-banner">{t("vendor.pendingApproval")}</p>
      )}

      <section className="vendor-section">
        <h2>{t("vendor.yourStall")}</h2>
        <form onSubmit={handleStallSubmit} className="experience-form">
          <label>{t("vendor.businessNameLabel")} <input value={stallForm.business_name} onChange={updateStall("business_name")} required /></label>
          <label>{t("vendor.description")} <textarea value={stallForm.description} onChange={updateStall("description")} /></label>
          <label>{t("vendor.cuisineType")} <input value={stallForm.cuisine_type} onChange={updateStall("cuisine_type")} /></label>
          <label>{t("vendor.address")} <input value={stallForm.address} onChange={updateStall("address")} /></label>
          <label>{t("vendor.phone")} <input value={stallForm.phone} onChange={updateStall("phone")} /></label>
          <label>{t("vendor.openingTime")} <input type="time" value={stallForm.opening_time} onChange={updateStall("opening_time")} /></label>
          <label>{t("vendor.closingTime")} <input type="time" value={stallForm.closing_time} onChange={updateStall("closing_time")} /></label>
          <label>{t("vendor.hoursNote")} <input value={stallForm.hours_note} onChange={updateStall("hours_note")} placeholder={t("vendor.hoursNotePlaceholder")} /></label>
          <button type="submit">{t("vendor.saveStall")}</button>
          {stallMessage && <p className="message">{stallMessage}</p>}
        </form>
      </section>

      <section className="vendor-section">
        <form onSubmit={handleSubmit} className="experience-form">
          <h2>{editingId ? t("vendor.editListing") : t("vendor.listNew")}</h2>
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
          <button type="submit">{editingId ? t("vendor.saveChanges") : t("vendor.publish")}</button>
          {editingId && (
            <button type="button" className="link-button" onClick={cancelEdit}>
              {t("vendor.cancelEdit")}
            </button>
          )}
          {message && <p className="message">{message}</p>}
        </form>

        <h2>{t("vendor.yourListings")}</h2>
        <ul className="vendor-list">
          {experiences.map((exp) => (
            <li key={exp.id} className="vendor-list-item">
              {exp.image && <img src={exp.image} alt={exp.title} className="vendor-list-thumb" />}
              <span>{exp.title} — ${exp.price} ({t(`category.${exp.category}`)})</span>
              <span className="vendor-list-actions">
                <button type="button" onClick={() => startEdit(exp)}>{t("vendor.edit")}</button>
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section className="vendor-section">
        <h2>{t("vendor.bookingsForYourStall")}</h2>
        {bookingMessage && <p className="error">{bookingMessage}</p>}
        <table className="vendor-bookings-table">
          <thead>
            <tr>
              <th>{t("bookings.experience")}</th>
              <th>{t("vendor.tourist")}</th>
              <th>{t("bookings.date")}</th>
              <th>{t("bookings.participants")}</th>
              <th>{t("bookings.total")}</th>
              <th>{t("bookings.status")}</th>
              <th>{t("vendor.actions")}</th>
            </tr>
          </thead>
          <tbody>
            {bookings.map((b) => (
              <tr key={b.id}>
                <td>{b.experience_title}</td>
                <td>{b.tourist.username}</td>
                <td>{new Date(b.booking_date).toLocaleString()}</td>
                <td>{b.number_of_participants}</td>
                <td>${b.total_price}</td>
                <td><span className={`status status-${b.status}`}>{t(`bookingStatus.${b.status}`)}</span></td>
                <td>
                  <span className="booking-actions">
                    {b.status === "pending" && (
                      <>
                        <button type="button" className="confirm" onClick={() => handleBookingAction(b.id, "confirmed")}>{t("vendor.confirm")}</button>
                        <button type="button" className="cancel" onClick={() => handleBookingAction(b.id, "cancelled")}>{t("vendor.decline")}</button>
                      </>
                    )}
                    {b.status === "confirmed" && (
                      <>
                        <button type="button" className="complete" onClick={() => handleBookingAction(b.id, "completed")}>{t("vendor.markCompleted")}</button>
                        <button type="button" className="cancel" onClick={() => handleBookingAction(b.id, "cancelled")}>{t("vendor.cancel")}</button>
                      </>
                    )}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {bookings.length === 0 && <p className="muted">{t("vendor.noBookings")}</p>}
      </section>
    </div>
  );
}
