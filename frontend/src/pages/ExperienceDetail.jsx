import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import client from "../api/client.js";
import ReviewList from "../components/ReviewList.jsx";
import LocationMap from "../components/LocationMap.jsx";
import { useAuth } from "../context/AuthContext.jsx";

export default function ExperienceDetail() {
  const { id } = useParams();
  const { isAuthenticated } = useAuth();
  const [experience, setExperience] = useState(null);
  const [bookingDate, setBookingDate] = useState("");
  const [participants, setParticipants] = useState(1);
  const [message, setMessage] = useState("");
  const [savedId, setSavedId] = useState(null); // id of the SavedExperience row, if saved
  const [inTrip, setInTrip] = useState(false);
  const [actionMessage, setActionMessage] = useState("");

  useEffect(() => {
    client.get(`/experiences/${id}/`).then(({ data }) => setExperience(data));
  }, [id]);

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
      setActionMessage("Please log in to save experiences.");
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
      setActionMessage("Please log in to plan a trip.");
      return;
    }
    if (inTrip) return;
    await client.post("/itinerary/", { experience: id });
    setInTrip(true);
    setActionMessage("Added to your trip.");
  }

  async function handleBooking(e) {
    e.preventDefault();
    setMessage("");
    if (!localStorage.getItem("access_token")) {
      setMessage("Please log in to book this experience.");
      return;
    }
    try {
      await client.post("/bookings/", {
        experience: id,
        booking_date: bookingDate,
        number_of_participants: participants,
      });
      setMessage("Booking request submitted! Check My Bookings for status.");
    } catch (err) {
      setMessage(err.response?.data?.detail || "Could not create booking. Check the form and try again.");
    }
  }

  if (!experience) return <p>Loading...</p>;

  return (
    <div className="detail-layout">
      <div>
        {experience.image && <img src={experience.image} alt={experience.title} className="detail-image" />}
        <h1>{experience.title}</h1>
        <p className="muted">by {experience.vendor?.business_name}</p>

        <div className="detail-actions">
          <button type="button" onClick={handleToggleSave} className={savedId ? "active" : ""}>
            {savedId ? "♥ Saved" : "♡ Save"}
          </button>
          <button type="button" onClick={handleAddToTrip} disabled={inTrip}>
            {inTrip ? "✓ In your trip" : "+ Add to Trip"}
          </button>
        </div>
        {actionMessage && <p className="message">{actionMessage}</p>}

        <p>{experience.description}</p>
        <p><strong>Duration:</strong> {experience.duration_minutes} minutes</p>
        <p><strong>Max participants:</strong> {experience.max_participants}</p>
        <p><strong>Price:</strong> ${experience.price} per person</p>
        {experience.address && <p><strong>Location:</strong> {experience.address}</p>}

        <LocationMap
          latitude={experience.latitude}
          longitude={experience.longitude}
          label={experience.title}
        />

        <h2>Reviews {experience.average_rating ? `(★ ${experience.average_rating})` : ""}</h2>
        <ReviewList reviews={experience.reviews} />
      </div>

      <form onSubmit={handleBooking} className="booking-form">
        <h2>Book this experience</h2>
        <label>
          Date &amp; time
          <input
            type="datetime-local"
            value={bookingDate}
            onChange={(e) => setBookingDate(e.target.value)}
            required
          />
        </label>
        <label>
          Participants
          <input
            type="number"
            min="1"
            max={experience.max_participants}
            value={participants}
            onChange={(e) => setParticipants(Number(e.target.value))}
          />
        </label>
        <p>Total: ${(experience.price * participants).toFixed(2)}</p>
        <button type="submit">Request booking</button>
        {message && <p className="message">{message}</p>}
      </form>
    </div>
  );
}
