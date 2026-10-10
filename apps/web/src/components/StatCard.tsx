export function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded border border-[var(--border)] bg-[var(--surface)] px-4 py-3">
      <div className="text-xs uppercase tracking-wide text-[var(--muted)]">{label}</div>
      <div className="mt-1 font-mono text-2xl text-[var(--foreground)]">{value}</div>
    </div>
  );
}
