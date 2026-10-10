export function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex min-h-[40vh] flex-col items-center justify-center gap-2 text-center">
      <p className="text-[var(--muted)]">{message}</p>
      <p className="text-xs text-[var(--muted)]">
        Select a repository above, or add one if the list is empty.
      </p>
    </div>
  );
}
