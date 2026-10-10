"use client";

import { useEffect, useState } from "react";
import { api, type RepoStatus } from "@/lib/api";
import { useRepo } from "@/lib/repo-context";
import { StatCard } from "@/components/StatCard";
import { ErrorBanner } from "@/components/ErrorBanner";
import { EmptyState } from "@/components/EmptyState";

export default function DashboardPage() {
  const { selected, loading: repoLoading, error: repoError } = useRepo();
  const [status, setStatus] = useState<RepoStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [indexing, setIndexing] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    setError(null);
    api
      .getStatus(selected.id)
      .then(setStatus)
      .catch((err) => {
        setStatus(null);
        setError(err instanceof Error ? err.message : "Failed to load status");
      })
      .finally(() => setLoading(false));
  }, [selected]);

  async function handleReindex() {
    if (!selected) return;
    setIndexing(true);
    setError(null);
    try {
      await api.indexRepository(selected.id);
      const s = await api.getStatus(selected.id);
      setStatus(s);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Indexing failed");
    } finally {
      setIndexing(false);
    }
  }

  if (repoError) return <ErrorBanner message={repoError} />;
  if (repoLoading) return <p className="text-[var(--muted)]">Loading...</p>;
  if (!selected) return <EmptyState message="No repository selected." />;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-mono text-lg">{selected.path}</h1>
          <p className="text-xs text-[var(--muted)]">repository id: {selected.id}</p>
        </div>
        <button
          onClick={handleReindex}
          disabled={indexing}
          className="rounded bg-[var(--accent)] px-3 py-1.5 text-sm font-medium text-[#0b0d10] disabled:opacity-50"
        >
          {indexing ? "Indexing..." : "Re-index"}
        </button>
      </div>

      {error && <ErrorBanner message={error} />}

      {loading && <p className="text-[var(--muted)]">Loading status...</p>}

      {!loading && status && (
        <>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <StatCard label="Files" value={status.total_files} />
            <StatCard label="Symbols" value={status.total_symbols} />
            <StatCard label="Relationships" value={status.total_relationships} />
            <StatCard
              label="Resolved"
              value={`${status.resolved_relationships}/${status.total_relationships}`}
            />
          </div>

          <div className="rounded border border-[var(--border)] bg-[var(--surface)] p-4">
            <h2 className="mb-2 text-sm font-medium text-[var(--muted)]">Languages</h2>
            <div className="flex flex-wrap gap-2">
              {Object.entries(status.files_by_language).map(([lang, count]) => (
                <span
                  key={lang}
                  className="rounded border border-[var(--border)] px-2 py-1 font-mono text-xs"
                >
                  {lang}: {count}
                </span>
              ))}
            </div>
          </div>

          <div className="rounded border border-[var(--border)] bg-[var(--surface)] p-4">
            <h2 className="mb-2 text-sm font-medium text-[var(--muted)]">Symbols by kind</h2>
            <div className="flex flex-wrap gap-2">
              {Object.entries(status.symbols_by_kind).map(([kind, count]) => (
                <span
                  key={kind}
                  className="rounded border border-[var(--border)] px-2 py-1 font-mono text-xs"
                >
                  {kind}: {count}
                </span>
              ))}
            </div>
          </div>

          <p className="text-xs text-[var(--muted)]">
            Last indexed: {status.last_indexed_at ?? "never"}
          </p>
        </>
      )}

      {!loading && !status && !error && (
        <EmptyState message="This repository has not been indexed yet. Click Re-index above." />
      )}
    </div>
  );
}
