import { useEffect, useState } from "react";
import { api } from "@/api/client";
import Skeleton from "./Skeleton";
import { Card } from "./ui/card";

type Props = {
  propertyId: string;
};

function formatStatus(status: string) {
  return status
    .split("_")
    .map(
      (word) =>
        word.charAt(0).toUpperCase() +
        word.slice(1)
    )
    .join(" ");
}

function formatSource(source: string) {
  const map: Record<string, string> = {
    booking_com: "Booking.com",
    mmt: "MakeMyTrip",
    agoda: "Agoda",
    direct: "Direct",
  };

  return map[source] ?? source;
}

function getStatusColor(status: string) {
  switch (status) {
    case "confirmed":
      return "bg-green-500";

    case "cancelled":
      return "bg-red-500";

    case "checked_out":
      return "bg-blue-500";

    case "no_show":
      return "bg-yellow-500";

    default:
      return "bg-zinc-500";
  }
}

function formatRoom(room: string) {
  return room.charAt(0).toUpperCase() +
         room.slice(1);
}

export default function BookingsTable({
  propertyId,
}: Props) {

  const [bookings, setBookings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadBookings(initial = false) {
  if (!propertyId) return;

  try {
    if (initial) setLoading(true);

    const res = await api.get("/bookings", {
      params: {
        property_id: propertyId,
      },
    });

    setBookings(res.data.items);
  } catch {
    setError("Failed to load bookings");
  } finally {
    if (initial) setLoading(false);
  }
}

useEffect(() => {
  if (!propertyId) return;

  loadBookings(true);

  const id = setInterval(
    () => loadBookings(false),
    30000
  );

  return () => clearInterval(id);
}, [propertyId]);

if (!propertyId) {
  return (
    <div className="glass rounded-3xl p-6 h-[250px] lg:h-[450px] flex items-center justify-center">
      <div className="text-center">
        <div className="text-4xl mb-2">📋</div>
              <h3 className="font-semibold text-lg">
        No Property Loaded
      </h3>
              <p className="mt-2 text-zinc-500">
        Enter a property ID to view activity.
      </p>
      </div>
    </div>
  );
}

if (loading) {
  return <Skeleton className="h-[300px]" />;
}

if (!bookings.length) {
  return (
    <div className="glass rounded-3xl p-6">
      No bookings found
    </div>
  );
}

  return (
<div className="glass rounded-3xl p-6">
  <h2 className="mb-6 text-2xl font-semibold">
    Bookings Overview
  </h2>

  {/* Mobile */}
  <div className="space-y-2 md:hidden max-h-[500px] overflow-y-auto [scrollbar-width:none]">
    {bookings.map((booking) => (
      <Card
        key={booking.booking_id}
        className="mx-1 mt-2.5 border-zinc-800 bg-zinc-900/40 p-3 rounded-2xl"
      >
        <div className="flex items-center justify-between">
          <span className="font-semibold text-base">
            {formatRoom(booking.room_type)}
          </span>

          <span className="font-semibold text-base">
            ₹{booking.amount_inr.toLocaleString("en-IN")}
          </span>
        </div>

        <div className="mt-2 flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <div
              className={`h-2 w-2 rounded-full ${getStatusColor(
                booking.status
              )}`}
            />

            {formatStatus(booking.status)}
          </div>

          <span>
            {formatSource(booking.source)}
          </span>
        </div>
      </Card>
    ))}
  </div>

  {/* Desktop */}
  <div className="hidden md:block max-h-[500px] overflow-auto   scrollbar-thin
  scrollbar-track-transparent">
    <table className="w-full">
      <thead>
        <tr className="border-b border-zinc-800">
          <th className="py-3 text-left">
            Room
          </th>

          <th className="py-3 text-left">
            Status
          </th>

          <th className="py-3 text-left">
            Amount
          </th>

          <th className="py-3 text-left">
            Source
          </th>
        </tr>
      </thead>

      <tbody>
        {bookings.map((booking) => (
          <tr
            key={booking.booking_id}
            className="border-b border-zinc-900"
          >
            <td className="py-4">
              {formatRoom(booking.room_type)}
            </td>

            <td className="py-4">
              <div className="flex items-center gap-2">
                <div
                  className={`h-2 w-2 rounded-full ${getStatusColor(
                    booking.status
                  )}`}
                />

                {formatStatus(booking.status)}
              </div>
            </td>

            <td className="py-4">
              ₹
              {booking.amount_inr.toLocaleString(
                "en-IN"
              )}
            </td>

            <td className="py-4">
              {formatSource(booking.source)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
</div>
  );
}