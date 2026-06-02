import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { api } from "@/api/client";

type Props = {
  propertyId: string;
};

type AskResponse = {
  answer: string;
  sql?: string | null;
  rows?: any[];
  citation?: string;
};

export default function AssistantPanel({
  propertyId,
}: Props) {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] =
    useState<AskResponse | null>(null);

  async function askAssistant() {
    if (!propertyId) {
      setError("Load a property first");
      return;
    }

    if (!question.trim()) {
      return;
    }

    try {
      setLoading(true);
      setError("");

      setResult(null);
      const res = await api.post("/ask", {
        property_id: propertyId,
        question,
      });
      setError("");
      setResult(res.data);
    } catch (err: any) {
      setResult(null);
      setError(
        err?.response?.data?.detail ??
        "Assistant request failed"
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="glass rounded-3xl p-6  lg:h-[650px] flex flex-col">
      <h2 className="mb-5 text-2xl font-semibold">
        Ask Assistant
      </h2>

      <Textarea
        rows={3}
        value={question}
        onChange={(e) =>
          setQuestion(e.target.value)
        }
        placeholder="How many bookings do I have?"
        className="bg-zinc-900"
      />

      <Button
        className="mt-4 w-full h-11"
        onClick={askAssistant}
        disabled={loading}
      >
        {loading ? "Thinking..." : "Ask"}
      </Button>

      {error && (
        <div className="mt-4 rounded-xl border border-red-900 bg-red-950/30 p-3 text-sm text-red-300">
          {error}
        </div>
      )}

      <div className="mt-6 flex-1 space-y-4 overflow-auto">
        <Card className="mx-2 mt-2 border-zinc-800 bg-zinc-900/50 p-4 rounded-2xl">
          <p className="mb-3 text-xs uppercase tracking-wider text-zinc-500">
            Assistant Response
          </p>

          {result ? (
            <div className="space-y-3">
              <p className="text-zinc-200">
                {result.answer}
              </p>

              {result.citation && (
                <div className="text-xs text-blue-400">
                  Citation: {result.citation}
                </div>
              )}
            </div>
          ) : (
            <div className="flex min-h-[120px] items-center justify-center text-center text-zinc-500">
              Ask about bookings, revenue,
              occupancy, WiFi, onboarding,
              rates, reviews, etc.
            </div>
          )}
        </Card>

        <Card className="mx-2 mb-3 border-zinc-800 bg-zinc-900/50 p-4 rounded-2xl">
          <p className="text-xs uppercase tracking-wider text-zinc-500">
            SQL Executed
          </p>

          <div className="max-h-[220px] overflow-auto rounded-xl bg-black/20 p-3">
            <code className="block whitespace-pre-wrap break-words text-sm text-zinc-400">
              {result?.sql ??
                "No SQL executed (RAG answer or no query yet)"}
            </code>
          </div>
        </Card>
      </div>
    </Card>
  );
}