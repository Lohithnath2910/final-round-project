import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import Skeleton from "./Skeleton";
import { api } from "@/api/client";

type Props = {
  propertyId: string;
};

function formatDate(date: string) {
  return new Date(date).toLocaleString(
    "en-IN",
    {
      timeZone: "Asia/Kolkata",
      day: "numeric",
      month: "short",
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    }
  );
}

function timeAgo(date: Date | null) {
  if (!date) return "Never";

  const seconds = Math.floor(
    (Date.now() - date.getTime()) / 1000
  );

  if (seconds < 60) return `${seconds}s ago`;

  const minutes = Math.floor(seconds / 60);

  return `${minutes}m ago`;
}

export default function EventsFeed({ propertyId }: Props) {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [, forceUpdate] = useState(0);

      useEffect(() => {
        const id = setInterval(() => {
          forceUpdate((x) => x + 1);
        }, 1000);

        return () => clearInterval(id);
      }, []);
  async function loadEvents(initial = false) {
    if (!propertyId) return;

    try {
      if(initial) 
        {
          setLoading(true);
        }
      setError("");

      const res = await api.get("/events", {
        params: {
          property_id: propertyId,
        },
      });

      setEvents(res.data.events);
      setLastUpdated(new Date());
    } catch {
      setError("Failed to load events");
    } finally {
      if (initial){
      setLoading(false);
      }  
    }
  }

  useEffect(() => {
    if (!propertyId) return;
    loadEvents(true);

    const id = setInterval(
      () => loadEvents(false), 10000);

    return () => clearInterval(id);
  }, [propertyId]);
  if (!propertyId)
return (
  <Card className="glass rounded-3xl p-6 min-h-[250px] lg:min-h-[650px] flex items-center justify-center">
    <div className="text-center">
      <div className="text-5xl mb-4">🏨</div>

      <h3 className="font-semibold text-lg">
        No Property Loaded
      </h3>

      <p className="mt-2 text-zinc-500">
        Enter a property ID to view activity.
      </p>
    </div>
  </Card>
);


  if (loading)
    return <Skeleton className="h-80" />;

  if (error)
    return (
      <Card className="glass rounded-3xl p-6">
        {error}
      </Card>
    );

    const EVENT_LABELS: Record<string, string> = {
  booking_requested: "Booking Request",
  cancellation_requested: "Cancellation Request",
  complaint_received: "Complaint Received",
  wakeup_requested: "Wake-up Call",
  faq_received: "FAQ Question",
  needs_human: "Needs Human Review",
  confirmation_required: "Confirmation Required",
  property_created: "Property Created",
};


  return (
    <Card className="gglass rounded-3xl p-6 h-fit lg:h-[650px] flex flex-col">
    <div className="mb-6 flex items-center justify-between">
      <h2 className="text-2xl font-semibold">
        Recent Activity
      </h2>

      <span className="text-xs text-zinc-500">
        Updated {timeAgo(lastUpdated)}
      </span>
    </div>

      <div className="max-h-[520px] overflow-y-auto space-y-4 pr-2">
        {events.map((event) => (
          <div
            key={event.event_id}
            className="rounded-xl border border-zinc-800 p-4"
          >
            <p className="font-semibold">
              {EVENT_LABELS[event.event_type] ??
              event.event_type}
            </p>

            <p className="text-sm text-zinc-400">
              {formatDate(event.created_at)}
            </p>
          </div>
        ))}
      </div>
    </Card>
  );
}