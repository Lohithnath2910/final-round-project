import { Card, CardContent } from "@/components/ui/card";
import { useEffect, useState } from "react";
import { api } from "@/api/client";

type Props = {
  propertyId: string;
};


export default function StatsBar({
  propertyId,
}: Props) {
  const [stats, setStats] = useState([
    { value: "--", label: "Bookings" },
    { value: "--", label: "Confirmed" },
    { value: "--", label: "Complaints" },
    { value: "--", label: "Handoffs" },
  ]);

useEffect(() => {
  if (!propertyId) return;

  async function loadStats() {
    try {
      const [bookingsRes, eventsRes] =
        await Promise.all([
          api.get("/bookings", {
            params: { property_id: propertyId },
          }),
          api.get("/events", {
            params: { property_id: propertyId },
          }),
        ]);

      const bookings =
        bookingsRes.data.items;

      const events =
        eventsRes.data.events;

      setStats([
        {
          value: bookings.length,
          label: "Bookings",
        },
        {
          value: bookings.filter(
            (booking: any) =>
              booking.status === "confirmed"
          ).length,
          label: "Confirmed",
        },
        {
          value: events.filter(
            (event: any) =>
              event.event_type ===
              "complaint_received"
          ).length,
          label: "Complaints",
        },
        {
          value: events.filter(
            (e: any) =>
              e.event_type ===
              "needs_human"
          ).length,
          label: "Handoffs",
        },
      ]);
    } catch {}
  }

  loadStats();

  const id = setInterval(
    loadStats,
    30000
  );

  return () => clearInterval(id);
}, [propertyId]);


if (!propertyId) {
  return (
    <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">
      {stats.map((item) => (
        <Card key={item.label}>
          <CardContent className="p-5">
            <div className="text-3xl font-bold">
              --
            </div>
            <div>{item.label}</div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

  return (
    <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">
      {stats.map((item) => (
        <Card
          key={item.label}
          className="glass rounded-3xl border-zinc-800"
        >
          <CardContent className="p-5">
            <div className="text-3xl font-bold text-white">
              {item.value}
            </div>

            <div className="mt-2 text-sm text-zinc-500">
              {item.label}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}