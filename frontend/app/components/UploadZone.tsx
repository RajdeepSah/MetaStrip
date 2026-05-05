"use client";

import { useCallback } from "react";
import { useDropzone } from "react-dropzone";

const ACCEPTED_TYPES = {
  "image/jpeg": [".jpg", ".jpeg"],
  "image/png": [".png"],
  "image/tiff": [".tif", ".tiff"],
  "image/heic": [".heic"],
  "application/pdf": [".pdf"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
};

interface Props {
  onUpload: (file: File) => void;
  disabled: boolean;
}

export function UploadZone({ onUpload, disabled }: Props) {
  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted[0]) onUpload(accepted[0]);
    },
    [onUpload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxFiles: 1,
    maxSize: 25 * 1024 * 1024,
    disabled,
  });

  return (
    <div
      {...getRootProps()}
      className={[
        "border-2 border-dashed rounded-xl p-12 text-center transition-all select-none",
        isDragActive
          ? "border-cyan-primary bg-cyan-ghost border-cyan-glow"
          : "border-border-dim hover:border-border-bright hover:bg-surface",
        disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer",
      ].join(" ")}
    >
      <input {...getInputProps()} />
      <div className="flex flex-col items-center gap-4">
        <UploadIcon active={isDragActive} />
        {disabled ? (
          <p className="font-mono text-cyan-primary text-sm">Analyzing…</p>
        ) : isDragActive ? (
          <p className="font-mono text-cyan-primary text-sm">Drop to analyze</p>
        ) : (
          <>
            <p className="font-mono text-text-primary text-sm">
              Drag & drop a file, or{" "}
              <span className="text-cyan-primary">click to browse</span>
            </p>
            <p className="font-mono text-text-muted text-xs tracking-wide">
              JPEG · PNG · TIFF · HEIC · PDF · DOCX · max 25 MB
            </p>
          </>
        )}
      </div>
    </div>
  );
}

function UploadIcon({ active }: { active: boolean }) {
  return (
    <svg
      width="44"
      height="44"
      viewBox="0 0 24 24"
      fill="none"
      className={active ? "text-cyan-primary" : "text-border-bright"}
    >
      <path
        d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <polyline
        points="17 8 12 3 7 8"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <line
        x1="12"
        y1="3"
        x2="12"
        y2="15"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
