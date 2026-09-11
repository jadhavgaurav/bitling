"use client";

export function Toast({ message }: { message: string | null }) {
  return (
    <div className={`toast-notice${message ? " show" : ""}`}>
      <span>⚡</span> {message}
    </div>
  );
}
