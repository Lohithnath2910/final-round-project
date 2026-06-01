import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function PropertyBar() {
  return (
    <div className="glass mb-6 rounded-3xl p-4">
      <label className="mb-2 block text-xs uppercase tracking-widest text-zinc-500">
        Property ID
      </label>

      <div className="flex flex-col gap-3 sm:flex-row">
        <Input
          placeholder="Enter property_id"
          className="h-12 bg-zinc-900"
        />

        <Button className="h-12 px-8">
          Load
        </Button>
      </div>
    </div>
  );
}