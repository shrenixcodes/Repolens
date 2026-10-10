"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { RepoPicker } from "@/components/RepoPicker";

const LINKS = [
  { href: "/", label: "Dashboard" },
  { href: "/explorer", label: "Explorer" },
  { href: "/search", label: "Search" },
  { href: "/ask", label: "Ask" },
  { href: "/graph", label: "Graph" },
  { href: "/impact", label: "Impact" },
  { href: "/history", label: "History" },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <header className="border-b border-[var(--border)] bg-[var(--surface)]">
      <div className="mx-auto flex max-w-7xl items-center gap-6 px-4 py-2.5">
        <Link href="/" className="font-mono text-sm font-semibold text-[var(--foreground)] no-underline">
          repolens<span className="text-[var(--accent)]">.</span>
        </Link>
        <nav className="flex items-center gap-1 text-sm">
          {LINKS.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded px-2.5 py-1 no-underline transition-colors ${
                  active
                    ? "bg-[var(--surface-hover)] text-[var(--accent-strong)]"
                    : "text-[var(--muted)] hover:bg-[var(--surface-hover)] hover:text-[var(--foreground)]"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
        <div className="ml-auto">
          <RepoPicker />
        </div>
      </div>
    </header>
  );
}
