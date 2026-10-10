// Thin typed client for the RepoLens API. Every function hits a real
// endpoint -- there is no mocked/fabricated data path in this file.

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // response body wasn't JSON; fall back to statusText
    }
    throw new ApiError(response.status, detail);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export interface Repository {
  id: string;
  path: string;
  created_at: string;
}

export interface IndexResult {
  files_scanned: number;
  files_indexed: number;
  files_unchanged: number;
  files_removed: number;
  files_failed: number;
  errors: { path: string; message: string }[];
}

export interface RepoStatus {
  total_files: number;
  total_symbols: number;
  total_relationships: number;
  resolved_relationships: number;
  files_by_language: Record<string, number>;
  symbols_by_kind: Record<string, number>;
  last_indexed_at: string | null;
}

export interface SearchResultItem {
  file_path: string;
  symbol: string | null;
  start_line: number;
  end_line: number;
  snippet: string;
  score: number;
}

export interface Citation {
  path: string;
  start_line: number;
  end_line: number;
  symbol: string | null;
  excerpt: string | null;
}

export interface RelatedSymbol {
  path: string;
  qualified_name: string;
  relation: string;
}

export interface AskResponse {
  answer: string;
  grounded: boolean;
  citations: Citation[];
  related_symbols: RelatedSymbol[];
}

export interface ImpactResponse {
  target: string;
  target_found: boolean;
  direct_dependents: string[];
  transitive_dependents: string[];
  related_tests: string[];
  limitations: string[];
}

export interface GraphNode {
  id: string;
  node_type: string;
  label: string;
  path: string | null;
  kind: string | null;
}

export interface GraphEdge {
  source: string;
  target: string;
  kind: string;
  resolution: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  truncated: boolean;
}

export interface SymbolInfo {
  id: number;
  file_path: string;
  name: string;
  qualified_name: string;
  kind: string;
  start_line: number;
  end_line: number;
  docstring: string | null;
  parent_qualified_name: string | null;
  decorators: string[];
  is_exported: boolean;
}

export interface FileDetail {
  path: string;
  language: string | null;
  size_bytes: number;
  content: string | null;
  symbols: SymbolInfo[];
}

export interface Commit {
  sha: string;
  author_name: string;
  author_email: string;
  date: string;
  subject: string;
}

export interface GitHistoryResponse {
  path: string;
  commits: Commit[];
}

export const api = {
  listRepositories: () => request<Repository[]>("/repositories"),
  registerRepository: (path: string) =>
    request<Repository>("/repositories", {
      method: "POST",
      body: JSON.stringify({ path }),
    }),
  indexRepository: (id: string) =>
    request<IndexResult>(`/repositories/${id}/index`, { method: "POST" }),
  getStatus: (id: string) => request<RepoStatus>(`/repositories/${id}/status`),
  search: (id: string, query: string, limit = 20) =>
    request<SearchResultItem[]>(`/repositories/${id}/search`, {
      method: "POST",
      body: JSON.stringify({ query, limit }),
    }),
  ask: (id: string, question: string) =>
    request<AskResponse>(`/repositories/${id}/ask`, {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
  analyzeImpact: (id: string, target: string) =>
    request<ImpactResponse>(`/repositories/${id}/impact`, {
      method: "POST",
      body: JSON.stringify({ target }),
    }),
  getGraph: (id: string, includeSymbols = false) =>
    request<GraphData>(
      `/repositories/${id}/graph?include_symbols=${includeSymbols}`,
    ),
  listFiles: (id: string) => request<string[]>(`/repositories/${id}/files`),
  getFile: (id: string, path: string) =>
    request<FileDetail>(
      `/repositories/${id}/files/${path.split("/").map(encodeURIComponent).join("/")}`,
    ),
  getGitHistory: (id: string, path: string, limit = 20) =>
    request<GitHistoryResponse>(
      `/repositories/${id}/git/history?path=${encodeURIComponent(path)}&limit=${limit}`,
    ),
};
