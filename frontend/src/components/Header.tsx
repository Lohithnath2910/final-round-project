export default function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-zinc-800 bg-zinc-950/80 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between p-4">
        <div>
          <h1 className="text-xl font-semibold">
            Hospitality Owner Console
          </h1>
          <p className="text-sm text-zinc-400">
            Multi-Tenant Operations Dashboard
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-emerald-500" />
          <span className="text-sm text-zinc-400">
            Live
          </span>
        </div>
      </div>
    </header>
  );
}