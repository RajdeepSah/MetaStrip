"use client";

import { useEffect, useState } from "react";

type BackendStatus = "checking" | "online" | "offline";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:5000";

export default function Home() {
  const [status, setStatus] = useState<BackendStatus>("checking");

  useEffect(() => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);

    fetch(`${BACKEND_URL}/api/health`, { signal: controller.signal })
      .then((res) => res.json())
      .then((data: { status: string }) => {
        setStatus(data.status === "ok" ? "online" : "offline");
      })
      .catch(() => setStatus("offline"))
      .finally(() => clearTimeout(timeout));
  }, []);

  const statusColor =
    status === "online"
      ? "text-risk-green"
      : status === "offline"
        ? "text-risk-red"
        : "text-risk-amber";

  const statusDot =
    status === "online"
      ? "bg-risk-green"
      : status === "offline"
        ? "bg-risk-red"
        : "bg-risk-amber animate-pulse";

  return (
    <main className="min-h-screen bg-grid flex flex-col items-center justify-center px-4">
      {/* Header */}
      <div className="text-center mb-16">
        <p className="font-mono text-cyan-dim text-sm tracking-[0.3em] uppercase mb-3">
          Metadata Exposure Audit
        </p>

        <h1 className="font-mono text-6xl font-semibold text-cyan-primary text-cyan-glow mb-4 tracking-tight">
          MetaStrip
        </h1>

        <p className="text-text-muted text-lg max-w-md mx-auto leading-relaxed">
          Upload a file. See exactly what it reveals about you.
          <br />
          Download it clean.
        </p>
      </div>

      {/* Backend status indicator */}
      <div className="border border-border-dim bg-surface rounded-lg px-6 py-4 flex items-center gap-3 font-mono text-sm">
        <div className={`w-2 h-2 rounded-full ${statusDot}`} />
        <span className="text-text-muted">Backend API</span>
        <span className="text-border-bright">·</span>
        <span className={statusColor}>
          {status === "checking" ? "connecting..." : status}
        </span>
        {status === "online" && (
          <span className="text-text-dim ml-1">
            {BACKEND_URL.replace("http://", "")}
          </span>
        )}
      </div>

      {/* Phase placeholder */}
      <div className="mt-16 border border-border-dim border-dashed rounded-lg px-12 py-8 text-center">
        <p className="font-mono text-text-muted text-sm">
          // upload zone — Phase 2
        </p>
      </div>

      {/* Footer */}
      <footer className="absolute bottom-6 font-mono text-text-dim text-xs">
        v0.1-scaffold · Phase 1 complete
      </footer>
    </main>
  );
}
