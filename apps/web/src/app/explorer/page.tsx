"use client";

import { useEffect, useMemo, useState } from "react";
import { api, type FileDetail } from "@/lib/api";
import { useRepo } from "@/lib/repo-context";
import { EmptyState } from "@/components/EmptyState";
import { ErrorBanner } from "@/components/ErrorBanner";

export default function ExplorerPage() {
  const { selected } = useRepo();
  const [files, setFiles] = useState<string[]>([]);
  const [filter, setFilter] = useState("");
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [detail, setDetail] = useState<FileDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingList, setLoadingList] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    if (!selected) return;
    setFiles([]);
    setLoadingList(true);
    setError(null);
    api
      .listFiles(selected.id)
      .then((list) => setFiles(list.sort()))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to list files"))
      .finally(() => setLoadingList(false));
  }, [selected]);

  useEffect(() => {
    if (!selected || !selectedPath) return;
    setDetail(null);
    setLoadingDetail(true);
    api
      .getFile(selected.id, selectedPath)
      .then(setDetail)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load file"))
      .finally(() => setLoadingDetail(false));
  }, [selected, selectedPath]);

  const filteredFiles = useMemo(
    () => files.filter((f) => f.toLowerCase().includes(filter.toLowerCase())),
    [files, filter],
  );

  if (!selected) return <EmptyState message="No repository selected." />;

  return (
    <div className="grid grid-cols-[280px_1fr] gap-4" style={{ height: "calc(100vh - 140px)" }}>
      <div className="flex flex-col gap-2 overflow-hidden rounded border border-[var(--border)] bg-[var(--surface)]">
        <div className="border-b border-[var(--border)] p-2">
          <input
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter files..."
            className="w-full rounded border border-[var(--border)] bg-[var(--background)] px-2 py-1 font-mono text-xs outline-none focus:border-[var(--accent)]"
          />
        </div>
        <div className="scrollbar-thin flex-1 overflow-y-auto">
          {loadingList && <p className="p-2 text-xs text-[var(--muted)]">Loading...</p>}
          {filteredFiles.map((f) => (
            <button
              key={f}
              onClick={() => setSelectedPath(f)}
              className={`block w-full truncate px-2 py-1 text-left font-mono text-xs ${
                selectedPath === f
                  ? "bg-[var(--surface-hover)] text-[var(--accent-strong)]"
                  : "text-[var(--foreground)] hover:bg-[var(--surface-hover)]"
              }`}
              title={f}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <div className="scrollbar-thin overflow-y-auto rounded border border-[var(--border)] bg-[var(--surface)] p-4">
        {error && <ErrorBanner message={error} />}
        {!selectedPath && <p className="text-sm text-[var(--muted)]">Select a file.</p>}
        {loadingDetail && <p className="text-sm text-[var(--muted)]">Loading...</p>}
        {detail && !loadingDetail && (
          <div className="flex flex-col gap-4">
            <div>
              <h2 className="font-mono text-sm text-[var(--accent-strong)]">{detail.path}</h2>
              <p className="text-xs text-[var(--muted)]">
                {detail.language ?? "unknown"} - {detail.size_bytes} bytes
              </p>
            </div>

            {detail.symbols.length > 0 && (
              <div>
                <h3 className="mb-1 text-xs font-medium text-[var(--muted)]">
                  Symbols ({detail.symbols.length})
                </h3>
                <div className="flex flex-wrap gap-1">
                  {detail.symbols.map((s) => (
                    <span
                      key={s.id}
                      className="rounded border border-[var(--border)] px-1.5 py-0.5 font-mono text-xs"
                      title={s.docstring ?? undefined}
                    >
                      {s.kind}:{s.qualified_name}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {detail.content !== null ? (
              <pre className="scrollbar-thin overflow-x-auto rounded border border-[var(--border)] bg-[var(--background)] p-3 font-mono text-xs leading-5">
                {detail.content.split("\n").map((line, i) => (
                  <div key={i} className="flex gap-3">
                    <span className="w-8 shrink-0 select-none text-right text-[var(--muted)]">
                      {i + 1}
                    </span>
                    <span className="whitespace-pre-wrap break-all">{line}</span>
                  </div>
                ))}
              </pre>
            ) : (
              <p className="text-xs text-[var(--muted)]">
                Binary or non-UTF-8 content -- not displayed.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
