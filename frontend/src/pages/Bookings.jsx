import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import client from "../api/client.js";

export default function Bookings() {
  const { t } = useTranslation();
  const [bookings, setBookings] = useState([]);

  useEffect(() => {
    client.get("/bookings/").then(({ data }) => setBookings(data.results ?? data));
  }, []);

  return (
    <div>
      <h1>{t("bookings.title")}</h1>
      <table className="bookings-table">
        <thead>
          <tr>
            <th>{t("bookings.experience")}</th>
            <th>{t("bookings.date")}</th>
            <th>{t("bookings.participants")}</th>
            <th>{t("bookings.total")}</th>
            <th>{t("bookings.status")}</th>
          </tr>
        </thead>
        <tbody>
          {bookings.map((b) => (
            <tr key={b.id}>
              <td>{b.experience_title}</td>
              <td>{new Date(b.booking_date).toLocaleString()}</td>
              <td>{b.number_of_participants}</td>
              <td>${b.total_price}</td>
              <td><span className={`status status-${b.status}`}>{t(`bookingStatus.${b.status}`)}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
      {bookings.length === 0 && <p>{t("bookings.empty")}</p>}
    </div>
  );
}
