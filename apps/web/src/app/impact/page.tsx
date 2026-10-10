"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api, type ImpactResponse } from "@/lib/api";
import { useRepo } from "@/lib/repo-context";
import { EmptyState } from "@/components/EmptyState";
import { ErrorBanner } from "@/components/ErrorBanner";

export default function ImpactPage() {
  return (
    <Suspense fallback={<p className="text-sm text-[var(--muted)]">Loading...</p>}>
      <ImpactPageInner />
    </Suspense>
  );
}

function ImpactPageInner() {
  const { selected } = useRepo();
  const searchParams = useSearchParams();
  const [target, setTarget] = useState(searchParams.get("target") ?? "");
  const [result, setResult] = useState<ImpactResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runAnalysis(explicitTarget?: string) {
    const value = (explicitTarget ?? target).trim();
    if (!selected || !value) return;
    setLoading(true);
    setError(null);
    try {
      const r = await api.analyzeImpact(selected.id, value);
      setResult(r);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impact analysis failed");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const fromQuery = searchParams.get("target");
    if (!fromQuery || !selected) return;
    setTarget(fromQuery);
    void runAnalysis(fromQuery);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected, searchParams]);

  if (!selected) return <EmptyState message="No repository selected." />;

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-lg font-medium">Impact analysis</h1>
      <div className="flex gap-2">
        <input
          autoFocus
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && runAnalysis()}
          placeholder="src/auth/service.py or src/auth/service.py::ClassName.method"
          className="flex-1 rounded border border-[var(--border)] bg-[var(--surface)] px-3 py-2 font-mono text-sm outline-none focus:border-[var(--accent)]"
        />
        <button
          onClick={() => runAnalysis()}
          disabled={loading}
          className="rounded bg-[var(--accent)] px-4 py-2 text-sm font-medium text-[#0b0d10] disabled:opacity-50"
        >
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </div>

      {error && <ErrorBanner message={error} />}

      {result && !result.target_found && (
        <p className="text-sm text-[var(--warn)]">&apos;{result.target}&apos; was not found in the index.</p>
      )}

      {result && result.target_found && (
        <div className="flex flex-col gap-3">
          <div className="grid grid-cols-3 gap-3">
            <div className="rounded border border-[var(--border)] bg-[var(--surface)] p-3">
              <div className="text-xs text-[var(--muted)]">Direct dependents</div>
              <div className="font-mono text-xl">{result.direct_dependents.length}</div>
            </div>
            <div className="rounded border border-[var(--border)] bg-[var(--surface)] p-3">
              <div className="text-xs text-[var(--muted)]">Transitive dependents</div>
              <div className="font-mono text-xl">{result.transitive_dependents.length}</div>
            </div>
            <div className="rounded border border-[var(--border)] bg-[var(--surface)] p-3">
              <div className="text-xs text-[var(--muted)]">Related tests</div>
              <div className="font-mono text-xl">{result.related_tests.length}</div>
            </div>
          </div>

          <Section title="Potentially affected (direct)" items={result.direct_dependents} />
          <Section title="Potentially affected (transitive)" items={result.transitive_dependents} />
          <Section title="Related tests" items={result.related_tests} />

          <div className="rounded border border-[var(--warn)]/30 bg-[var(--warn)]/5 p-3 text-xs text-[var(--warn)]">
            <ul className="list-inside list-disc space-y-1">
              {result.limitations.map((l, i) => (
                <li key={i}>{l}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}

function Section({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div className="rounded border border-[var(--border)] bg-[var(--surface)] p-3">
      <h2 className="mb-2 text-sm font-medium text-[var(--muted)]">{title}</h2>
      <ul className="flex flex-col gap-1 font-mono text-xs">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
