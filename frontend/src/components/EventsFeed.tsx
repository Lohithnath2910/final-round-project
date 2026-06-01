import {
  CalendarPlus,
  AlarmClock,
  AlertCircle,
  UserRound,
} from "lucide-react";

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
    <div className="glass rounded-2xl p-5">
      <h2 className="mb-6 text-xl font-semibold">
        Recent Activity
      </h2>

      <div className="space-y-5">
        {events.map((event) => {
          const Icon = event.icon;

          return (
            <div
              key={event.title}
              className="flex gap-4"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500/10">
                <Icon
                  size={18}
                  className="text-blue-400"
                />
              </div>

              <div>
                <p className="font-medium">
                  {event.title}
                </p>

                <p className="mt-1 text-sm text-zinc-500">
                  Waiting for backend data
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}