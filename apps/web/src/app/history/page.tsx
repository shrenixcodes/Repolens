"use client";

import { useState } from "react";
import { api, type Commit } from "@/lib/api";
import { useRepo } from "@/lib/repo-context";
import { EmptyState } from "@/components/EmptyState";
import { ErrorBanner } from "@/components/ErrorBanner";

export default function HistoryPage() {
  const { selected } = useRepo();
  const [path, setPath] = useState("");
  const [commits, setCommits] = useState<Commit[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runLookup() {
    if (!selected || !path.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const r = await api.getGitHistory(selected.id, path.trim());
      setCommits(r.commits);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Git history lookup failed");
      setCommits(null);
    } finally {
      setLoading(false);
    }
  }

  if (!selected) return <EmptyState message="No repository selected." />;

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-lg font-medium">Git history</h1>
      <div className="flex gap-2">
        <input
          autoFocus
          value={path}
          onChange={(e) => setPath(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && runLookup()}
          placeholder="src/auth/service.py"
          className="flex-1 rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2 font-mono text-sm outline-none focus:border-[var(--accent)]"
        />
        <button
          onClick={runLookup}
          disabled={loading}
          className="rounded bg-[var(--accent)] px-4 py-2 text-sm font-medium text-[#0b0d10] disabled:opacity-50"
        >
          {loading ? "Loading..." : "Show history"}
        </button>
      </div>

      {error && <ErrorBanner message={error} />}

      {commits !== null && commits.length === 0 && (
        <p className="text-sm text-[var(--muted)]">No commit history found for this path.</p>
      )}

      <div className="flex flex-col gap-2">
        {commits?.map((c) => (
          <div key={c.sha} className="rounded border border-[var(--border)] bg-[var(--surface)] p-3">
            <div className="flex items-center justify-between font-mono text-xs text-[var(--muted)]">
              <span>{c.sha.slice(0, 8)}</span>
              <span>{c.date}</span>
            </div>
            <p className="mt-1 text-sm">{c.subject}</p>
            <p className="mt-1 text-xs text-[var(--muted)]">
              {c.author_name} &lt;{c.author_email}&gt;
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
