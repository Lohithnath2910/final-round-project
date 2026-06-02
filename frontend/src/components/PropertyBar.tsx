import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

type Props = {
  inputProperty: string;
  setInputProperty: React.Dispatch<React.SetStateAction<string>>;
  onLoad: () => void;
};


export default function PropertyBar({
  inputProperty,
  setInputProperty,
  onLoad,
}: Props) {
  return (
    <div className="glass mb-6 rounded-3xl p-4">
      <label className="mb-2 block text-xs uppercase tracking-widest text-zinc-500">
        Property ID
      </label>

      <div className="flex flex-col gap-3 sm:flex-row">
        <Input
          value={inputProperty}
          onChange={(e) => setInputProperty(e.target.value)}
          placeholder="Enter property_id"
          className="h-12 bg-zinc-900"
        />

        <Button className="h-12 px-8" onClick={onLoad}>
          Load
        </Button>
      </div>
    </div>
  );
}