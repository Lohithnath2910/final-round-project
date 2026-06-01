import Header from "./components/Header";
import PropertyBar from "./components/PropertyBar";
import AssistantPanel from "./components/AssistantPanel";
import EventsFeed from "./components/EventsFeed";
import BookingsTable from "./components/BookingsTable";
import StatsBar from "./components/Statsbar";

export default function App() {
  return (
    <div className="min-h-screen">
      <div className="fixed inset-0 -z-10">
        <div className="absolute left-1/2 top-0 h-[450px] w-[450px] -translate-x-1/2 rounded-full bg-blue-600/10 blur-[150px]" />
        <div className="absolute bottom-0 right-0 h-[350px] w-[350px] rounded-full bg-indigo-600/10 blur-[150px]" />
      </div>
      <div className="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(circle_at_top,rgba(37,99,235,0.12),transparent_40%)]" />
      <main className="mx-auto max-w-6xl px-4 py-6 space-y-5">
        <Header />

        <PropertyBar />

        <StatsBar/>

        <AssistantPanel />

        <EventsFeed />

        <BookingsTable />
      </main>
    </div>
  );
}