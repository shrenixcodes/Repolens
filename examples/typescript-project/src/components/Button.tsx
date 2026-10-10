import type { ReactNode } from "react";

export interface ButtonProps {
  label: string;
  onClick: () => void;
  children?: ReactNode;
}

export function Button({ label, onClick, children }: ButtonProps) {
  return (
    <button onClick={onClick} aria-label={label}>
      {children ?? label}
    </button>
  );
}
