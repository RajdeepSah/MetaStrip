"use client";

import { useState } from "react";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:5000";

interface Props {
  fileId: string;
  filename: string;
}

export function DownloadButton({ fileId, filename }: Props) {
  const [loading, setLoading] = useState(false);

  async function handleDownload() {
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/download/${fileId}`);
      if (!res.ok) return;
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `cleaned_${filename}`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      onClick={handleDownload}
      disabled={loading}
      className={[
        "font-mono text-sm px-5 py-2.5 rounded-lg border transition-all shrink-0",
        loading
          ? "border-border-dim text-text-muted cursor-not-allowed"
          : "border-cyan-primary text-cyan-primary hover:bg-cyan-ghost border-cyan-glow",
      ].join(" ")}
    >
      {loading ? "Downloading…" : "↓ Download Clean File"}
    </button>
  );
}
