export default function PropertyBar() {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
      <div className="flex flex-col gap-3 md:flex-row">
        <input
          placeholder="Enter property_id"
          className="flex-1 rounded-xl border border-zinc-700 bg-zinc-950 px-4 py-3 outline-none"
        />

        <button
          className="rounded-xl bg-blue-600 px-6 py-3 font-medium"
        >
          Load
        </button>
      </div>
    </div>
  );
}