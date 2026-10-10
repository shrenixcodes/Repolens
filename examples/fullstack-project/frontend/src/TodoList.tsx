import { useEffect, useState } from "react";
import { completeTodo, fetchTodos, type Todo } from "./api";

export function TodoList() {
  const [todos, setTodos] = useState<Todo[]>([]);

  useEffect(() => {
    fetchTodos().then(setTodos);
  }, []);

  async function handleComplete(id: number) {
    const updated = await completeTodo(id);
    setTodos((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
  }

  return (
    <ul>
      {todos.map((todo) => (
        <li key={todo.id} style={{ textDecoration: todo.done ? "line-through" : "none" }}>
          {todo.title}
          {!todo.done && <button onClick={() => handleComplete(todo.id)}>Done</button>}
        </li>
      ))}
    </ul>
  );
}
