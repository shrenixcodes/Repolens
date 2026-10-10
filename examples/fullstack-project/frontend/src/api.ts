export interface Todo {
  id: number;
  title: string;
  done: boolean;
}

const API_BASE = "/api";

export async function fetchTodos(): Promise<Todo[]> {
  const response = await fetch(`${API_BASE}/todos`);
  return response.json();
}

export async function createTodo(title: string): Promise<Todo> {
  const response = await fetch(`${API_BASE}/todos`, {
    method: "POST",
    body: JSON.stringify({ title }),
  });
  return response.json();
}

export async function completeTodo(id: number): Promise<Todo> {
  const response = await fetch(`${API_BASE}/todos/${id}/complete`, { method: "POST" });
  return response.json();
}
