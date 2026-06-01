const stats = [
  { value: "--", label: "Bookings" },
  { value: "--", label: "Pending" },
  { value: "--", label: "Complaints" },
  { value: "--", label: "Handoffs" },
];

export default function StatsBar() {
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
      {stats.map((item) => (
        <div
          key={item.label}
          className="
            glass
            relative
            rounded-2xl
            p-5
            transition-all
            duration-300
            hover:-translate-y-1
          "
        >
          <div className="absolute right-4 top-4 h-2 w-2 rounded-full bg-blue-500" />

          <div className="text-4xl font-bold">
            {item.value}
          </div>

          <div className="mt-2 text-sm text-zinc-500">
            {item.label}
          </div>
        </div>
      ))}
    </div>
  );
}