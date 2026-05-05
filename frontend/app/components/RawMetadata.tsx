"use client";

import { useState } from "react";

interface Props {
  label: string;
  data: Record<string, unknown> | null | undefined;
}

export function RawMetadata({ label, data }: Props) {
  const [open, setOpen] = useState(false);

  if (!data || Object.keys(data).length === 0) return null;

  return (
    <div className="border border-border-dim rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-surface transition-colors"
      >
        <span className="font-mono text-xs text-text-muted uppercase tracking-widest">
          {label}
        </span>
        <span className="font-mono text-xs text-text-dim">
          {open ? "▲ collapse" : "▼ expand"}
        </span>
      </button>
      {open && (
        <pre className="px-4 pb-4 pt-1 font-mono text-xs text-text-primary overflow-x-auto bg-bg-dark leading-relaxed whitespace-pre-wrap break-all">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
}
