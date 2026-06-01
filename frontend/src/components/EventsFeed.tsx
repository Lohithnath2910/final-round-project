import {
  CalendarPlus,
  AlarmClock,
  AlertCircle,
  UserRound,
} from "lucide-react";

import { Card } from "@/components/ui/card";

const events = [
  {
    icon: CalendarPlus,
    title: "Booking Created",
  },
  {
    icon: AlertCircle,
    title: "Cancellation Request",
  },
  {
    icon: AlarmClock,
    title: "Wake-up Call",
  },
  {
    icon: UserRound,
    title: "Human Handoff",
  },
];

export default function EventsFeed() {
  return (
    <Card className="glass rounded-3xl p-6 h-fit">
      <h2 className="mb-6 text-2xl font-semibold">
        Recent Activity
      </h2>

      <div className="space-y-5">
        {events.map((event) => {
          const Icon = event.icon;

          return (
            <div
              key={event.title}
              className="flex items-center gap-5 rounded-2xl border border-zinc-800 bg-zinc-900/20 p-5 transition hover:bg-zinc-900/40"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-500/10">
                <Icon
                  size={18}
                  className="text-blue-400"
                />
              </div>

              <div>
                <p className="font-medium text-white">
                  {event.title}
                </p>

                <p className="text-sm text-zinc-400">
                  Waiting for backend data
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}