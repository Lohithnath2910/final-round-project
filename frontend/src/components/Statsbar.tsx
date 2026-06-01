import { Card, CardContent } from "@/components/ui/card";

const stats = [
  { value: "--", label: "Bookings" },
  { value: "--", label: "Pending" },
  { value: "--", label: "Complaints" },
  { value: "--", label: "Handoffs" },
];

export default function StatsBar() {
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