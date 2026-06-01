export default function BookingsTable() {
  return (
    <div className="glass rounded-2xl p-5">
      <h2 className="mb-5 text-xl font-semibold">
        Bookings Overview
      </h2>

      <div className="md:hidden">
        <div className="rounded-2xl bg-zinc-950 p-6 text-center text-zinc-500">
          📋
          <br />
          <br />
          No bookings found.
          <br />
          Load a property to view bookings.
        </div>
      </div>

      <div className="hidden overflow-x-auto md:block">
        <table className="w-full">
          <thead>
            <tr className="border-b border-zinc-800">
              <th className="py-3 text-left">Room</th>
              <th className="text-left">Status</th>
              <th className="text-left">Source</th>
              <th className="text-left">Amount</th>
            </tr>
          </thead>

          <tbody>
            <tr>
              <td
                colSpan={4}
                className="py-10 text-center text-zinc-500"
              >
                📋 No bookings found
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}