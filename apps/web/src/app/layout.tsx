import type { Metadata } from "next";
import "./globals.css";
import { Nav } from "@/components/Nav";
import { RepoProvider } from "@/lib/repo-context";

export const metadata: Metadata = {
  title: "RepoLens",
  description: "Local-first AI codebase intelligence",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="flex min-h-full flex-col">
        <RepoProvider>
          <Nav />
          <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6">{children}</main>
        </RepoProvider>
      </body>
    </html>
  );
}
