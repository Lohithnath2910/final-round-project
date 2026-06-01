export default function BookingsTable() {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">
      <h2 className="mb-4 text-lg font-semibold">
        Bookings
      </h2>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-zinc-800">
              <th className="py-3 text-left">
                Room Type
              </th>

              <th className="text-left">
                Status
              </th>

              <th className="text-left">
                Source
              </th>

              <th className="text-left">
                Amount
              </th>
            </tr>
          </thead>

          <tbody>
            <tr>
              <td
                colSpan={4}
                className="py-6 text-center text-zinc-500"
              >
                No bookings loaded
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}