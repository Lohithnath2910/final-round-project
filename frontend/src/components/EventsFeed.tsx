export default function EventsFeed() {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">
      <h2 className="mb-4 text-lg font-semibold">
        Lifecycle Feed
      </h2>

      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="rounded-xl border border-zinc-800 bg-zinc-950 p-4"
          >
            <p className="font-medium">
              booking_requested
            </p>

            <p className="mt-1 text-sm text-zinc-400">
              Waiting for backend data...
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}