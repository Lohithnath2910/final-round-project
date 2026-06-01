export default function BookingsTable() {
  return (
    <div className="glass rounded-3xl p-6">
      <h2 className="mb-6 text-2xl font-semibold">
        Bookings Overview
      </h2>

      <div className="flex h-56 flex-col items-center justify-center text-center">
        <div className="mb-3 text-4xl">
          📋
        </div>

        <p className="font-medium text-zinc-300">
          No bookings available
        </p>

        <p className="mt-1 text-sm text-zinc-500">
          Load a property to view reservations
        </p>
      </div>
    </div>
  );
}