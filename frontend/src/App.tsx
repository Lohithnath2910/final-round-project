import Header from "./components/Header";
import PropertyBar from "./components/PropertyBar";
import EventsFeed from "./components/EventsFeed";
import AssistantPanel from "./components/AssistantPanel";
import BookingsTable from "./components/BookingsTable";

export default function App() {
  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <Header />

      <main className="mx-auto max-w-7xl p-4 space-y-6">
        <PropertyBar />

        <div className="grid gap-6 lg:grid-cols-12">
          <div className="lg:col-span-8">
            <EventsFeed />
          </div>

          <div className="lg:col-span-4">
            <AssistantPanel />
          </div>
        </div>

        <BookingsTable />
      </main>
    </div>
  );
}