export default function AssistantPanel() {
  return (
    <div className="glass rounded-2xl p-5">
      <h2 className="mb-4 text-xl font-semibold">
        Ask Assistant
      </h2>

      <textarea
        rows={2}
        placeholder="How many bookings do I have today?"
        className="
          w-full
          rounded-2xl
          border
          border-zinc-700
          bg-zinc-950
          p-4
          outline-none
          transition
          focus:border-blue-500
          focus:ring-2
          focus:ring-blue-500/20
        "
      />

      <button
        className="
          mt-3
          w-full
          rounded-2xl
          bg-blue-600
          py-3
          font-medium
          transition
          hover:bg-blue-500
        "
      >
        Ask
      </button>

      <div className="mt-5 space-y-4">
        <div className="rounded-2xl bg-zinc-950 p-4">
          <p className="mb-2 text-xs uppercase tracking-wider text-zinc-500">
            Answer
          </p>

          <div className="py-6 text-center text-zinc-500">
            💬
            <br />
            <br />
            Ask a question about bookings,
            occupancy, revenue or operations.
          </div>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-black/60 p-4">
          <p className="mb-2 text-xs uppercase tracking-wider text-zinc-500">
            SQL Executed
          </p>

          <code className="font-mono text-sm text-zinc-400">
            Waiting for query...
          </code>
        </div>
      </div>
    </div>
  );
}