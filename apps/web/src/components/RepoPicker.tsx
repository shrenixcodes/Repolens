"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useRepo } from "@/lib/repo-context";

export function RepoPicker() {
  const { repositories, selectedId, selectRepository, refresh } = useRepo();
  const [adding, setAdding] = useState(false);
  const [newPath, setNewPath] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAdd() {
    if (!newPath.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const repo = await api.registerRepository(newPath.trim());
      await api.indexRepository(repo.id);
      await refresh();
      selectRepository(repo.id);
      setAdding(false);
      setNewPath("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to register repository");
    } finally {
      setBusy(false);
    }
  }

  if (adding) {
    return (
      <div className="flex items-center gap-2">
        <input
          autoFocus
          value={newPath}
          onChange={(e) => setNewPath(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAdd()}
          placeholder="/absolute/path/to/repo"
          className="w-64 rounded border border-[var(--border)] bg-[var(--background)] px-2 py-1 font-mono text-xs text-[var(--foreground)] outline-none focus:border-[var(--accent)]"
        />
        <button
          onClick={handleAdd}
          disabled={busy}
          className="rounded bg-[var(--accent)] px-2 py-1 text-xs font-medium text-[#0b0d10] disabled:opacity-50"
        >
          {busy ? "Indexing..." : "Add + Index"}
        </button>
        <button
          onClick={() => setAdding(false)}
          className="text-xs text-[var(--muted)] hover:text-[var(--foreground)]"
        >
          Cancel
        </button>
        {error && <span className="text-xs text-[var(--danger)]">{error}</span>}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <select
        value={selectedId ?? ""}
        onChange={(e) => selectRepository(e.target.value)}
        className="rounded border border-[var(--border)] bg-[var(--background)] px-2 py-1 font-mono text-xs text-[var(--foreground)] outline-none focus:border-[var(--accent)]"
      >
        <option value="" disabled>
          {repositories.length === 0 ? "No repositories" : "Select repository"}
        </option>
        {repositories.map((r) => (
          <option key={r.id} value={r.id}>
            {r.path}
          </option>
        ))}
      </select>
      <button
        onClick={() => setAdding(true)}
        className="rounded border border-[var(--border)] px-2 py-1 text-xs text-[var(--muted)] hover:text-[var(--foreground)]"
      >
        + Add
      </button>
    </div>
  );
}
