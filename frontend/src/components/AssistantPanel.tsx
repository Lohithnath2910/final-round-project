import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";

export default function AssistantPanel() {
  return (
    <Card className="glass rounded-3xl p-6 h-fit">
      <h2 className="mb-5 text-2xl font-semibold">
        Ask Assistant
      </h2>

      <Textarea
        rows={3}
        placeholder="How many bookings do I have today?"
        className="bg-zinc-900"
      />

      <Button className="mt-4 w-full h-11">
        Ask
      </Button>

      <div className="mt-6 space-y-4">
        <Card className="border-zinc-800 bg-zinc-900/50 p-5">
          <p className="mb-3 text-xs uppercase tracking-wider text-zinc-500">
            Assistant Response
          </p>

          <div className="flex min-h-[120px] items-center justify-center text-center text-zinc-500">
            Ask a question about bookings,
            occupancy, revenue or operations.
          </div>
        </Card>

        <Card className="border-zinc-800 bg-zinc-900/50 p-5">
          <p className="mb-3 text-xs uppercase tracking-wider text-zinc-500">
            SQL Executed
          </p>

          <code className="font-mono text-sm text-zinc-400">
            Waiting for query...
          </code>
        </Card>
      </div>
    </Card>
  );
}