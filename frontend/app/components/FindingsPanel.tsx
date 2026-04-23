import {
  AuditResponse,
  ImageFindings,
  PdfFindings,
  DocxFindings,
} from "../lib/types";
import { SensitivityRing } from "./SensitivityRing";
import { RiskList } from "./RiskList";
import { RawMetadata } from "./RawMetadata";
import { DownloadButton } from "./DownloadButton";

interface Props {
  data: AuditResponse;
  onReset: () => void;
}

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(2)} MB`;
}

function MetaRow({
  label,
  value,
}: {
  label: string;
  value?: string | number | boolean | null;
}) {
  if (value === null || value === undefined || value === "") return null;
  return (
    <div className="flex gap-3 py-1.5 border-b border-border-dim last:border-0">
      <span className="font-mono text-xs text-text-muted w-44 shrink-0">
        {label}
      </span>
      <span className="font-mono text-xs text-text-primary break-all">
        {typeof value === "boolean" ? (value ? "yes" : "no") : String(value)}
      </span>
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="border border-border-dim rounded-lg overflow-hidden">
      <div className="px-4 py-2 bg-surface border-b border-border-dim">
        <h3 className="font-mono text-xs text-text-muted uppercase tracking-widest">
          {title}
        </h3>
      </div>
      <div className="px-4 py-2">{children}</div>
    </div>
  );
}

function ImageSections({ f }: { f: ImageFindings }) {
  const hasCamera = f.camera && Object.keys(f.camera).length > 0;
  const hasTimestamps = f.timestamps && Object.keys(f.timestamps).length > 0;

  return (
    <>
      {f.gps && (
        <Section title="GPS Location">
          <MetaRow label="Latitude" value={f.gps.lat.toFixed(6)} />
          <MetaRow label="Longitude" value={f.gps.lon.toFixed(6)} />
          {f.gps.altitude !== undefined && (
            <MetaRow label="Altitude" value={`${f.gps.altitude.toFixed(1)} m`} />
          )}
        </Section>
      )}
      {(f.author || f.thumbnail_embedded || hasCamera) && (
        <Section title="Camera & Author">
          <MetaRow label="Author / Artist" value={f.author} />
          <MetaRow
            label="Thumbnail embedded"
            value={f.thumbnail_embedded ? "yes" : null}
          />
          {hasCamera &&
            Object.entries(f.camera!).map(([k, v]) => (
              <MetaRow key={k} label={k} value={String(v)} />
            ))}
        </Section>
      )}
      {hasTimestamps && (
        <Section title="Timestamps">
          {Object.entries(f.timestamps!).map(([k, v]) => (
            <MetaRow key={k} label={k} value={String(v)} />
          ))}
        </Section>
      )}
      <RawMetadata
        label="Raw EXIF data"
        data={f.raw_exif as Record<string, unknown>}
      />
    </>
  );
}

function PdfSections({ f }: { f: PdfFindings }) {
  return (
    <>
      <Section title="Document Properties">
        <MetaRow label="Author" value={f.author} />
        <MetaRow label="Title" value={f.title} />
        <MetaRow label="Subject" value={f.subject} />
        <MetaRow label="Keywords" value={f.keywords} />
        <MetaRow label="Creator tool" value={f.creator_tool} />
        <MetaRow label="Producer" value={f.producer} />
        <MetaRow label="Creation date" value={f.creation_date} />
        <MetaRow label="Modification date" value={f.modification_date} />
      </Section>
      <Section title="PDF Structure">
        <MetaRow label="PDF version" value={f.pdf_version} />
        <MetaRow label="Pages" value={f.pages} />
        <MetaRow label="Contains JavaScript" value={f.has_javascript} />
        <MetaRow label="Incremental updates" value={f.has_incremental_updates} />
        <MetaRow label="Embedded files" value={f.embedded_file_count} />
        <MetaRow
          label="Form fields"
          value={f.form_fields?.join(", ") || null}
        />
        <MetaRow
          label="Embedded fonts"
          value={
            f.embedded_fonts && f.embedded_fonts.length > 0
              ? `${f.embedded_fonts.length} font(s)`
              : null
          }
        />
      </Section>
      <RawMetadata label="Raw PDF metadata" data={f.raw_metadata} />
    </>
  );
}

function DocxSections({ f }: { f: DocxFindings }) {
  return (
    <>
      <Section title="Author Information">
        <MetaRow label="Author" value={f.author} />
        <MetaRow label="Last modified by" value={f.last_modified_by} />
        <MetaRow label="Company" value={f.company} />
      </Section>
      <Section title="Document Statistics">
        <MetaRow label="Title" value={f.title} />
        <MetaRow label="Subject" value={f.subject} />
        <MetaRow label="Description" value={f.description} />
        <MetaRow label="Category" value={f.category} />
        <MetaRow label="Revision" value={f.revision} />
        <MetaRow label="Created" value={f.created} />
        <MetaRow label="Modified" value={f.modified} />
        <MetaRow label="Editing time (min)" value={f.total_editing_time} />
        <MetaRow label="Tracked changes" value={f.tracked_changes_count} />
        <MetaRow label="Comments" value={f.comments_count} />
        <MetaRow label="Embedded images" value={f.embedded_image_count} />
        <MetaRow label="App name" value={f.app_name} />
        <MetaRow label="App version" value={f.app_version} />
      </Section>
      <RawMetadata label="Raw core properties" data={f.raw_core_props} />
      <RawMetadata label="Raw app properties" data={f.raw_app_props} />
    </>
  );
}

export function FindingsPanel({ data, onReset }: Props) {
  const { file_type, findings } = data;
  const isImage = file_type.startsWith("image/");
  const isPdf = file_type === "application/pdf";

  const sizeSavingPct =
    data.cleaned_size !== undefined
      ? Math.round((1 - data.cleaned_size / data.file_size) * 100)
      : null;

  const imgF = findings as ImageFindings;

  return (
    <div className="space-y-5">
      {/* Summary card */}
      <div className="flex flex-wrap gap-6 items-center border border-border-dim rounded-xl p-6 bg-surface">
        <SensitivityRing score={data.sensitivity_score} />

        <div className="flex-1 min-w-[180px] space-y-0.5">
          <MetaRow label="File" value={data.filename} />
          <MetaRow label="Original size" value={formatBytes(data.file_size)} />
          {data.cleaned_size !== undefined && (
            <MetaRow
              label="Cleaned size"
              value={`${formatBytes(data.cleaned_size)}${
                sizeSavingPct !== null && sizeSavingPct > 0
                  ? ` (−${sizeSavingPct}%)`
                  : ""
              }`}
            />
          )}
          {isImage && imgF.gps && (
            <MetaRow
              label="GPS"
              value={`${imgF.gps.lat.toFixed(5)}, ${imgF.gps.lon.toFixed(5)}`}
            />
          )}
          {isPdf && (findings as PdfFindings).pages !== undefined && (
            <MetaRow label="Pages" value={(findings as PdfFindings).pages} />
          )}
        </div>

        <div className="flex flex-col gap-2 items-end shrink-0">
          {data.cleaned_file_id && (
            <DownloadButton
              fileId={data.cleaned_file_id}
              filename={data.filename}
            />
          )}
          {data.strip_error && (
            <p className="font-mono text-xs text-risk-amber max-w-xs text-right">
              Strip failed: {data.strip_error}
            </p>
          )}
          <button
            onClick={onReset}
            className="font-mono text-xs text-text-muted hover:text-text-primary transition-colors"
          >
            ← Analyze another file
          </button>
        </div>
      </div>

      {/* Risk factors */}
      <Section title="Risk Factors">
        <RiskList risks={data.risks} />
      </Section>

      {/* Type-specific metadata */}
      {isImage && <ImageSections f={findings as ImageFindings} />}
      {isPdf && <PdfSections f={findings as PdfFindings} />}
      {!isImage && !isPdf && <DocxSections f={findings as DocxFindings} />}
    </div>
  );
}
