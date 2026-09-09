import { useState } from "react";
import { useTranslation } from "react-i18next";
import client from "../api/client.js";
import ExperienceCard from "../components/ExperienceCard.jsx";

export default function TripPlanner() {
  const { t } = useTranslation();
  const [messages, setMessages] = useState([
    { from: "assistant", text: t("tripPlanner.intro") },
  ]);
  const [input, setInput] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [addStatus, setAddStatus] = useState("");

  async function handleSend(e) {
    e.preventDefault();
    const message = input.trim();
    if (!message) return;

    setMessages((prev) => [...prev, { from: "user", text: message }]);
    setInput("");
    setLoading(true);
    setAddStatus("");

    try {
      const { data } = await client.post("/experiences/plan-trip/", { message });
      setMessages((prev) => [...prev, { from: "assistant", text: data.reply }]);
      setSuggestions(data.experiences);
    } catch {
      setMessages((prev) => [...prev, { from: "assistant", text: t("tripPlanner.error") }]);
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  }

  async function handleAddAllToTrip() {
    setAddStatus("");
    try {
      await Promise.all(
        suggestions.map((exp) => client.post("/itinerary/", { experience: exp.id }).catch(() => null))
      );
      setAddStatus(t("tripPlanner.addedAll"));
    } catch {
      setAddStatus(t("tripPlanner.addFailed"));
    }
  }

  return (
    <div className="trip-planner">
      <h1>{t("tripPlanner.title")}</h1>
      <p className="muted">{t("tripPlanner.disclaimer")}</p>

      <div className="chat-window">
        {messages.map((m, i) => (
          <div key={i} className={`chat-bubble chat-bubble-${m.from}`}>
            {m.text}
          </div>
        ))}
        {loading && <div className="chat-bubble chat-bubble-assistant">{t("common.loading")}</div>}
      </div>

      <form onSubmit={handleSend} className="chat-input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t("tripPlanner.inputPlaceholder")}
        />
        <button type="submit" disabled={loading}>{t("tripPlanner.send")}</button>
      </form>

      {suggestions.length > 0 && (
        <div className="trip-planner-results">
          <div className="experience-grid">
            {suggestions.map((exp) => (
              <ExperienceCard key={exp.id} experience={exp} />
            ))}
          </div>
          <button type="button" onClick={handleAddAllToTrip}>{t("tripPlanner.addAllToTrip")}</button>
          {addStatus && <p className="message">{addStatus}</p>}
        </div>
      )}
    </div>
  );
}
