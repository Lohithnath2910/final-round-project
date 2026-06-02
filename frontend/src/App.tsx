import Header from "./components/Header";
import PropertyBar from "./components/PropertyBar";
import AssistantPanel from "./components/AssistantPanel";
import EventsFeed from "./components/EventsFeed";
import BookingsTable from "./components/BookingsTable";
import StatsBar from "./components/Statsbar";
import { useState } from "react";


export default function App() {
  const [inputProperty, setInputProperty] = useState("");
  const [propertyId, setPropertyId] = useState("");

  return (
    <div className="min-h-screen bg-[#09090b]">
      <div className="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(circle_at_top,rgba(37,99,235,0.12),transparent_40%)]" />

      <main className="mx-auto max-w-7xl px-4 py-8">
        <Header />

        <div className="mt-8">
          <PropertyBar 
          inputProperty = {inputProperty}
          setInputProperty = {setInputProperty}
          onLoad={() => setPropertyId(inputProperty)}/>
        </div>

        <div className="mt-5">
          <StatsBar propertyId={propertyId}/>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.35fr_1fr] lg:items-start">
          <EventsFeed propertyId={propertyId}/>
          <AssistantPanel propertyId={propertyId}/>
        </div>

        <div className="mt-6">
          <BookingsTable propertyId={propertyId}/>
        </div>
      </main>
    </div>
  );
}