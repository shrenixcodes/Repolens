export function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="rounded border border-[var(--danger)]/40 bg-[var(--danger)]/10 px-3 py-2 text-sm text-[var(--danger)]">
      {message}
    </div>
  );
}
