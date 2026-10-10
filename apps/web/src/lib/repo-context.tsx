"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { api, type Repository } from "@/lib/api";

const STORAGE_KEY = "repolens.selectedRepositoryId";

interface RepoContextValue {
  repositories: Repository[];
  selectedId: string | null;
  selected: Repository | null;
  loading: boolean;
  error: string | null;
  selectRepository: (id: string) => void;
  refresh: () => Promise<void>;
}

const RepoContext = createContext<RepoContextValue | null>(null);

export function RepoProvider({ children }: { children: ReactNode }) {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const repos = await api.listRepositories();
      setRepositories(repos);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reach the RepoLens API");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    setSelectedId(window.localStorage.getItem(STORAGE_KEY));
    void refresh();
  }, [refresh]);

  const selectRepository = useCallback((id: string) => {
    setSelectedId(id);
    window.localStorage.setItem(STORAGE_KEY, id);
  }, []);

  const selected = repositories.find((r) => r.id === selectedId) ?? null;

  return (
    <RepoContext.Provider
      value={{ repositories, selectedId, selected, loading, error, selectRepository, refresh }}
    >
      {children}
    </RepoContext.Provider>
  );
}

export function useRepo(): RepoContextValue {
  const ctx = useContext(RepoContext);
  if (!ctx) throw new Error("useRepo must be used within a RepoProvider");
  return ctx;
}
