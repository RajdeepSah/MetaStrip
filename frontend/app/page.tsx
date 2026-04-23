"use client";

import { useCallback, useReducer } from "react";
import { UploadZone } from "./components/UploadZone";
import { FindingsPanel } from "./components/FindingsPanel";
import { AuditResponse } from "./lib/types";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:5000";

type State =
  | { phase: "idle" }
  | { phase: "uploading" }
  | { phase: "results"; data: AuditResponse }
  | { phase: "error"; message: string };

type Action =
  | { type: "UPLOAD_START" }
  | { type: "UPLOAD_SUCCESS"; data: AuditResponse }
  | { type: "UPLOAD_ERROR"; message: string }
  | { type: "RESET" };

function reducer(_: State, action: Action): State {
  switch (action.type) {
    case "UPLOAD_START":   return { phase: "uploading" };
    case "UPLOAD_SUCCESS": return { phase: "results", data: action.data };
    case "UPLOAD_ERROR":   return { phase: "error", message: action.message };
    case "RESET":          return { phase: "idle" };
  }
}

export default function Home() {
  const [state, dispatch] = useReducer(reducer, { phase: "idle" });

  const handleUpload = useCallback(async (file: File) => {
    dispatch({ type: "UPLOAD_START" });
    const form = new FormData();
    form.append("file", file);

    try {
      const res = await fetch(`${BACKEND_URL}/api/audit`, {
        method: "POST",
        body: form,
      });
      const json = await res.json();
      if (!res.ok) {
        dispatch({
          type: "UPLOAD_ERROR",
          message: (json as { error?: string }).error ?? `HTTP ${res.status}`,
        });
        return;
      }
      dispatch({ type: "UPLOAD_SUCCESS", data: json as AuditResponse });
    } catch {
      dispatch({
        type: "UPLOAD_ERROR",
        message: "Network error — is the backend running?",
      });
    }
  }, []);

  const handleReset = useCallback(() => dispatch({ type: "RESET" }), []);

  return (
    <main className="min-h-screen bg-grid px-4 py-12">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="text-center mb-10">
          <p className="font-mono text-cyan-dim text-xs tracking-[0.3em] uppercase mb-3">
            Metadata Exposure Audit
          </p>
          <h1 className="font-mono text-5xl font-semibold text-cyan-primary text-cyan-glow mb-3 tracking-tight">
            MetaStrip
          </h1>
          <p className="text-text-muted text-sm max-w-sm mx-auto leading-relaxed">
            Upload a file. See exactly what it reveals about you.
            Download it clean.
          </p>
        </div>

        {/* Content */}
        {state.phase === "idle" && (
          <UploadZone onUpload={handleUpload} disabled={false} />
        )}

        {state.phase === "uploading" && (
          <UploadZone onUpload={handleUpload} disabled={true} />
        )}

        {state.phase === "error" && (
          <div className="space-y-4">
            <div className="border border-risk-red/30 bg-surface rounded-xl p-6 text-center">
              <p className="font-mono text-risk-red text-sm mb-1">
                Analysis failed
              </p>
              <p className="font-mono text-text-muted text-xs">
                {state.message}
              </p>
            </div>
            <button
              onClick={handleReset}
              className="w-full font-mono text-sm text-text-muted hover:text-text-primary transition-colors py-2"
            >
              ← Try again
            </button>
          </div>
        )}

        {state.phase === "results" && (
          <FindingsPanel data={state.data} onReset={handleReset} />
        )}
      </div>

      <footer className="text-center mt-16 font-mono text-text-dim text-xs">
        v0.5 · Phase 5 complete
      </footer>
    </main>
  );
}
