export default function AssistantPanel() {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">
      <h2 className="mb-4 text-lg font-semibold">
        Ask Assistant
      </h2>

      <textarea
        rows={5}
        placeholder="Show bookings count"
        className="w-full rounded-xl border border-zinc-700 bg-zinc-950 p-3"
      />

      <button className="mt-3 w-full rounded-xl bg-blue-600 py-3">
        Ask
      </button>

      <div className="mt-4 rounded-xl border border-zinc-800 bg-zinc-950 p-3">
        <p className="text-zinc-500">
          No answer yet
        </p>
      </div>
    </div>
  );
}