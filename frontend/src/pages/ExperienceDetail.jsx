import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import client from "../api/client.js";
import ReviewList from "../components/ReviewList.jsx";
import ReviewForm from "../components/ReviewForm.jsx";
import LocationMap from "../components/LocationMap.jsx";
import { useAuth } from "../context/AuthContext.jsx";

export default function ExperienceDetail() {
  const { t, i18n } = useTranslation();
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [experience, setExperience] = useState(null);
  const [bookingDate, setBookingDate] = useState("");
  const [participants, setParticipants] = useState(1);
  const [message, setMessage] = useState("");
  const [savedId, setSavedId] = useState(null); // id of the SavedExperience row, if saved
  const [inTrip, setInTrip] = useState(false);
  const [actionMessage, setActionMessage] = useState("");

  useEffect(() => {
    loadExperience();
  }, [id, i18n.language]);

  function loadExperience() {
    client.get(`/experiences/${id}/`).then(({ data }) => setExperience(data));
  }

  // Check saved/trip status once logged in -- these are small personal lists,
  // fine to fetch and search client-side rather than adding a dedicated endpoint.
  useEffect(() => {
    if (!isAuthenticated) return;
    client.get("/saved/").then(({ data }) => {
      const match = (data.results ?? data).find((s) => String(s.experience) === String(id));
      setSavedId(match ? match.id : null);
    });
    client.get("/itinerary/").then(({ data }) => {
      const match = (data.results ?? data).find((s) => String(s.experience) === String(id));
      setInTrip(!!match);
    });
  }, [id, isAuthenticated]);

  async function handleToggleSave() {
    if (!isAuthenticated) {
      setActionMessage(t("detail.loginToSave"));
      return;
    }
    if (savedId) {
      await client.delete(`/saved/${savedId}/`);
      setSavedId(null);
    } else {
      const { data } = await client.post("/saved/", { experience: id });
      setSavedId(data.id);
    }
  }

  async function handleAddToTrip() {
    if (!isAuthenticated) {
      setActionMessage(t("detail.loginToPlan"));
      return;
    }
    if (inTrip) return;
    await client.post("/itinerary/", { experience: id });
    setInTrip(true);
    setActionMessage(t("detail.addedToTrip"));
  }

  async function handleBooking(e) {
    e.preventDefault();
    setMessage("");
    if (!localStorage.getItem("access_token")) {
      setMessage(t("detail.loginToBook"));
      return;
    }
    try {
      await client.post("/bookings/", {
        experience: id,
        booking_date: bookingDate,
        number_of_participants: participants,
      });
      setMessage(t("detail.bookingSubmitted"));
    } catch (err) {
      setMessage(err.response?.data?.detail || t("detail.bookingError"));
    }
  }

  if (!experience) return <p>{t("common.loading")}</p>;

  return (
    <>
      <button type="button" className="back-button" onClick={() => navigate(-1)}>
        ← {t("detail.back")}
      </button>
      <div className="detail-layout">
      <div>
        {experience.image && <img src={experience.image} alt={experience.title} className="detail-image" />}
        <h1>{experience.title}</h1>
        <p className="muted">{t("detail.by", { name: experience.vendor?.business_name })}</p>

        <div className="detail-actions">
          <button type="button" onClick={handleToggleSave} className={savedId ? "active" : ""}>
            {savedId ? t("detail.saved") : t("detail.notSaved")}
          </button>
          <button type="button" onClick={handleAddToTrip} disabled={inTrip}>
            {inTrip ? t("detail.inTrip") : t("detail.addToTrip")}
          </button>
        </div>
        {actionMessage && <p className="message">{actionMessage}</p>}

        <p>{experience.description}</p>
        <p><strong>{t("detail.duration")}</strong> {experience.duration_minutes} {t("detail.minutes")}</p>
        <p><strong>{t("detail.maxParticipants")}</strong> {experience.max_participants}</p>
        <p><strong>{t("detail.price")}</strong> ${experience.price} {t("detail.perPerson")}</p>
        {experience.address && <p><strong>{t("detail.location")}</strong> {experience.address}</p>}
        {experience.vendor?.opening_time && experience.vendor?.closing_time && (
          <p>
            <strong>{t("detail.openingHours")}</strong>{" "}
            {experience.vendor.opening_time.slice(0, 5)}–{experience.vendor.closing_time.slice(0, 5)}
            {experience.vendor.hours_note && ` (${experience.vendor.hours_note})`}
          </p>
        )}

        <LocationMap
          latitude={experience.latitude}
          longitude={experience.longitude}
          label={experience.title}
        />

        <h2>{t("detail.reviews")} {experience.average_rating ? `(★ ${experience.average_rating})` : ""}</h2>
        <ReviewForm experienceId={id} onReviewAdded={loadExperience} />
        <ReviewList reviews={experience.reviews} />
      </div>

      <form onSubmit={handleBooking} className="booking-form">
        <h2>{t("detail.bookThisExperience")}</h2>
        <label>
          {t("detail.dateTime")}
          <input
            type="datetime-local"
            value={bookingDate}
            onChange={(e) => setBookingDate(e.target.value)}
            required
          />
        </label>
        <label>
          {t("detail.participants")}
          <input
            type="number"
            min="1"
            max={experience.max_participants}
            value={participants}
            onChange={(e) => setParticipants(Number(e.target.value))}
          />
        </label>
        <p>{t("detail.total")} ${(experience.price * participants).toFixed(2)}</p>
        <button type="submit">{t("detail.requestBooking")}</button>
        {message && <p className="message">{message}</p>}
      </form>
      </div>
    </>
  );
}
