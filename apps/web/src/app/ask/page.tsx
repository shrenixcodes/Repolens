"use client";

import { useState } from "react";
import { api, type AskResponse } from "@/lib/api";
import { useRepo } from "@/lib/repo-context";
import { EmptyState } from "@/components/EmptyState";
import { ErrorBanner } from "@/components/ErrorBanner";

interface Turn {
  question: string;
  response: AskResponse;
}

export default function AskPage() {
  const { selected } = useRepo();
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAsk() {
    if (!selected || !question.trim()) return;
    const q = question.trim();
    setLoading(true);
    setError(null);
    try {
      const response = await api.ask(selected.id, q);
      setTurns((prev) => [...prev, { question: q, response }]);
      setQuestion("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ask failed");
    } finally {
      setLoading(false);
    }
  }

  if (!selected) return <EmptyState message="No repository selected." />;

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-lg font-medium">Ask</h1>

      <div className="flex flex-col gap-4">
        {turns.map((turn, i) => (
          <div key={i} className="flex flex-col gap-2">
            <div className="self-start rounded border border-[var(--border)] bg-[var(--surface-hover)] px-3 py-2 text-sm">
              {turn.question}
            </div>
            <div className="flex flex-col gap-2 rounded border border-[var(--border)] bg-[var(--surface)] p-3">
              <p className="text-sm whitespace-pre-wrap">{turn.response.answer}</p>
              {!turn.response.grounded && (
                <p className="text-xs text-[var(--warn)]">No supporting evidence was found.</p>
              )}
              {turn.response.citations.length > 0 && (
                <div className="mt-1">
                  <h3 className="text-xs font-medium text-[var(--muted)]">Sources</h3>
                  <ul className="mt-1 flex flex-col gap-1">
                    {turn.response.citations.map((c, j) => (
                      <li key={j} className="font-mono text-xs text-[var(--accent-strong)]">
                        {c.path}:{c.start_line}-{c.end_line}
                        {c.symbol && <span className="text-[var(--muted)]"> ({c.symbol})</span>}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {turn.response.related_symbols.length > 0 && (
                <div className="mt-1">
                  <h3 className="text-xs font-medium text-[var(--muted)]">Related symbols</h3>
                  <ul className="mt-1 flex flex-wrap gap-2">
                    {turn.response.related_symbols.map((r, j) => (
                      <li
                        key={j}
                        className="rounded border border-[var(--border)] px-2 py-0.5 font-mono text-xs"
                      >
                        {r.qualified_name} ({r.relation})
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {error && <ErrorBanner message={error} />}

      <div className="flex gap-2">
        <input
          autoFocus
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAsk()}
          placeholder="Where is authentication implemented?"
          className="flex-1 rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm outline-none focus:border-[var(--accent)]"
        />
        <button
          onClick={handleAsk}
          disabled={loading}
          className="rounded bg-[var(--accent)] px-4 py-2 text-sm font-medium text-[#0b0d10] disabled:opacity-50"
        >
          {loading ? "Thinking..." : "Ask"}
        </button>
      </div>
    </div>
  );
}
