"use client";

import { useState } from "react";
import { api, type SearchResultItem } from "@/lib/api";
import { useRepo } from "@/lib/repo-context";
import { EmptyState } from "@/components/EmptyState";
import { ErrorBanner } from "@/components/ErrorBanner";

export default function SearchPage() {
  const { selected } = useRepo();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResultItem[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runSearch() {
    if (!selected || !query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const r = await api.search(selected.id, query.trim());
      setResults(r);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
      setResults(null);
    } finally {
      setLoading(false);
    }
  }

  if (!selected) return <EmptyState message="No repository selected." />;

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-lg font-medium">Search</h1>
      <div className="flex gap-2">
        <input
          autoFocus
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && runSearch()}
          placeholder="JWT authentication, verify_token, ..."
          className="flex-1 rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2 font-mono text-sm outline-none focus:border-[var(--accent)]"
        />
        <button
          onClick={runSearch}
          disabled={loading}
          className="rounded bg-[var(--accent)] px-4 py-2 text-sm font-medium text-[#0b0d10] disabled:opacity-50"
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      {error && <ErrorBanner message={error} />}

      {results !== null && results.length === 0 && (
        <p className="text-sm text-[var(--muted)]">No matches found.</p>
      )}

      <div className="flex flex-col gap-2">
        {results?.map((r, i) => (
          <div key={i} className="rounded border border-[var(--border)] bg-[var(--surface)] p-3">
            <div className="flex items-center justify-between font-mono text-xs text-[var(--accent-strong)]">
              <span>
                {r.file_path}:{r.start_line}-{r.end_line}
                {r.symbol && <span className="text-[var(--muted)]"> ({r.symbol})</span>}
              </span>
              <span className="text-[var(--muted)]">score {r.score.toFixed(2)}</span>
            </div>
            <pre className="scrollbar-thin mt-2 overflow-x-auto whitespace-pre-wrap font-mono text-xs text-[var(--foreground)]">
              {r.snippet}
            </pre>
          </div>
        ))}
      </div>
    </div>
  );
}
