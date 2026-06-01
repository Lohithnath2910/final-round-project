export default function PropertyBar() {
  return (
    <div className="glass rounded-2xl p-4">
      <label className="mb-2 block text-xs uppercase tracking-widest text-zinc-500">
        Property ID
      </label>

      <div className="flex flex-col gap-3 sm:flex-row">
        <input
          placeholder="Enter property_id"
          className="
            flex-1
            rounded-2xl
            border
            border-zinc-700
            bg-zinc-950
            px-4
            py-3
            outline-none
            transition
            focus:border-blue-500
            focus:ring-2
            focus:ring-blue-500/20
          "
        />

        <button
          className="
            rounded-2xl
            bg-blue-600
            px-6
            py-3
            font-medium
            transition
            hover:bg-blue-500
          "
        >
          Load
        </button>
      </div>
    </div>
  );
}